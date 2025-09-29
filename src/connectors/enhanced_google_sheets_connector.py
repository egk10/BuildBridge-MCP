"""Enhanced Google Sheets connector with formula awareness."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import networkx as nx

from connectors.google_sheets_connector import GoogleSheetsConnector
from models.formula_context import FormulaContext
from schema_discovery import FormulaClassifier, export_dependency_graph, analyze_dependency_graph
from utils.formula_metrics import get_formula_metrics_recorder


LOGGER = logging.getLogger(__name__)

CELL_REF_REGEX = re.compile(
	r"(?:'[^']+'!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+|:\$?[A-Z]{1,3}|:[A-Z]{1,3}\$?\d+|:[A-Z]{1,3})?",
	re.IGNORECASE,
)

RANGE_SANITIZE_REGEX = re.compile(r"[^A-Za-z0-9_-]+")

BUSINESS_RULE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
	"FINANCIAL_CALCULATION": ("SUM", "SUMIF", "SUMIFS", "AVERAGE", "PMT", "NPV", "IRR", "FV", "PV"),
	"BUSINESS_LOGIC": ("IF", "IFS", "SWITCH", "CHOOSE"),
	"DATA_LOOKUP": ("VLOOKUP", "HLOOKUP", "XLOOKUP", "INDEX", "MATCH", "OFFSET", "INDIRECT"),
	"FINANCIAL_MODEL": ("XIRR", "XNPV", "RATE", "IPMT"),
	"STATISTICAL_ANALYSIS": ("MEDIAN", "STDEV", "VAR", "AVERAGEIF", "COUNTIF", "COUNTIFS"),
}


@dataclass
class _CellEntry:
	sheet_title: str
	row_index: int  # 0-based
	column_index: int  # 0-based
	a1_address: str
	full_address: str
	formatted_value: Optional[str]
	effective_value: Any
	formula: Optional[str]
	dependencies: List[str]
	business_rule: Optional[str]
	data_validation: Optional[Dict[str, Any]]

	def to_formula_context(self, last_updated: str = "") -> FormulaContext:
		return FormulaContext(
			formula=self.formula,
			cell_address=self.full_address,
			dependencies=self.dependencies,
			calculated_value=self.effective_value,
			business_rule=self.business_rule or "",
			last_updated=last_updated,
		)

	def provenance(self) -> Dict[str, Any]:
		return {
			"sheet_title": self.sheet_title,
			"row": self.row_index + 1,
			"column": self.column_index + 1,
			"a1": self.a1_address,
		}


class EnhancedGoogleSheetsConnector(GoogleSheetsConnector):
	"""Formula-aware Google Sheets connector."""

	def __init__(self, config: Dict[str, Any], gcp_client: Optional[Any] = None):
		super().__init__(config)
		self.client = gcp_client
		self.logger = logging.getLogger(self.__class__.__name__)

		project_root = Path(__file__).resolve().parents[2]
		default_cache_dir = project_root / "cache" / "normalized" / "formulas"
		override_cache_dir = config.get("formula_cache_dir")
		self._formula_cache_dir = Path(override_cache_dir) if override_cache_dir else default_cache_dir
		self._formula_cache_dir.mkdir(parents=True, exist_ok=True)

		self._metrics = get_formula_metrics_recorder()

	# ------------------------------------------------------------------
	# Public API

	def get_comprehensive_sheet_context(
		self,
		sheet_id: str,
		range_name: Optional[str] = None,
		include_formulas: bool = True,
		force_refresh: bool = False,
	) -> Dict[str, Any]:
		"""Extract spreadsheet values, formulas, and metadata in one sweep."""

		actual_sheet_id = self._resolve_sheet_id(sheet_id)
		start_time = time.perf_counter()
		context: Dict[str, Any] = self._empty_context(actual_sheet_id, range_name)

		try:
			api_response = self._fetch_sheet_response(
				actual_sheet_id,
				range_name,
				include_formulas=include_formulas,
				force_refresh=force_refresh,
			)

			if not api_response:
				LOGGER.info("No API response available for %s; returning empty context", actual_sheet_id)
				success = False
			else:
				context = self._build_context_from_response(actual_sheet_id, range_name, api_response)
				self._persist_normalized_cache(actual_sheet_id, range_name, context)
				success = True

		except Exception as exc:  # pragma: no cover - defensive logging
			success = False
			context.setdefault("errors", []).append(str(exc))
			LOGGER.exception("Failed to build formula context for sheet %s", actual_sheet_id)
		finally:
			duration = time.perf_counter() - start_time
			metadata = context.get("metadata", {})
			total_cells = metadata.get("total_cells", 0)
			formula_cells = metadata.get("formula_cell_count", 0)
			missing_dependencies = metadata.get("missing_dependencies", 0)
			self._metrics.record(
				success=success,
				duration_seconds=duration,
				total_cells=total_cells,
				formula_cells=formula_cells,
				missing_dependencies=missing_dependencies,
			)

		return context

	# ------------------------------------------------------------------
	# API helpers

	def _fetch_sheet_response(
		self,
		sheet_id: str,
		range_name: Optional[str],
		*,
		include_formulas: bool,
		force_refresh: bool,
	) -> Dict[str, Any]:
		if self.local_mode or not self.service:
			# Local/dev mode: allow callers to stub response objects.
			return {}

		request_kwargs: Dict[str, Any] = {"spreadsheetId": sheet_id, "includeGridData": include_formulas}
		if range_name:
			request_kwargs["ranges"] = [range_name]

		return self.service.spreadsheets().get(**request_kwargs).execute()

	def _build_context_from_response(
		self,
		sheet_id: str,
		range_name: Optional[str],
		api_response: Dict[str, Any],
	) -> Dict[str, Any]:
		last_updated = self._lookup_last_updated(sheet_id)

		cell_entries = list(self._iter_cell_entries(api_response))
		raw_values: Dict[str, Dict[str, Any]] = {}
		formulas: Dict[str, Dict[str, str]] = {}
		business_rules: Dict[str, str] = {}
		data_validation: Dict[str, Dict[str, Any]] = {}
		dependency_map: Dict[str, List[str]] = {}
		contexts: List[Dict[str, Any]] = []

		for entry in cell_entries:
			sheet_title = entry.sheet_title
			raw_values.setdefault(sheet_title, {})[entry.a1_address] = entry.effective_value
			if entry.formula:
				formulas.setdefault(sheet_title, {})[entry.a1_address] = entry.formula
				dependency_map[entry.full_address] = entry.dependencies
				if entry.business_rule:
					business_rules[entry.full_address] = entry.business_rule
			if entry.data_validation:
				data_validation[entry.full_address] = entry.data_validation

			context_payload = entry.to_formula_context(last_updated).to_dict()
			context_payload["display_value"] = entry.formatted_value
			context_payload["provenance"] = entry.provenance()
			if entry.data_validation:
				context_payload["data_validation"] = entry.data_validation
			contexts.append(context_payload)

		dependency_graph = self._build_dependency_graph(dependency_map)
		missing_dependencies = self._find_missing_dependencies(dependency_map, raw_values)
		conditional_formatting = self._extract_conditional_formatting(api_response)

		metadata = self._extract_sheet_metadata(
			api_response,
			sheet_id,
			range_name,
			total_cells=len(cell_entries),
			formula_cells=sum(1 for e in cell_entries if e.formula),
			missing_dependencies=len(missing_dependencies),
			last_updated=last_updated,
			dependency_cycles=self._detect_cycles(dependency_graph),
		)

		return {
			"raw_values": raw_values,
			"formulas": formulas,
			"dependencies": dependency_graph,
			"business_rules": business_rules,
			"data_validation": data_validation,
			"conditional_formatting": conditional_formatting,
			"metadata": metadata,
			"missing_dependencies": sorted(missing_dependencies),
			"formula_contexts": contexts,
		}

	# ------------------------------------------------------------------
	# Extraction primitives

	def _iter_cell_entries(self, api_response: Dict[str, Any]) -> Iterable[_CellEntry]:
		for sheet in api_response.get("sheets", []):
			sheet_title = sheet.get("properties", {}).get("title", "Sheet1")

			for data_block in sheet.get("data", []):
				start_row = data_block.get("startRow", 0)
				start_column = data_block.get("startColumn", 0)
				for row_offset, row in enumerate(data_block.get("rowData", [])):
					values = row.get("values", [])
					for col_offset, cell in enumerate(values):
						row_index = start_row + row_offset
						column_index = start_column + col_offset
						a1_address = self._to_a1(row_index, column_index)
						full_address = f"{sheet_title}!{a1_address}"

						formula = self._extract_formula(cell)
						dependencies = self._parse_formula_dependencies(formula, sheet_title)
						business_rule = self._classify_business_rule(formula)
						formatted = cell.get("formattedValue")
						effective_value = self._extract_effective_value(cell)
						data_validation = self._summarize_data_validation(cell.get("dataValidation"))

						yield _CellEntry(
							sheet_title=sheet_title,
							row_index=row_index,
							column_index=column_index,
							a1_address=a1_address,
							full_address=full_address,
							formatted_value=formatted,
							effective_value=effective_value,
							formula=formula,
							dependencies=dependencies,
							business_rule=business_rule,
							data_validation=data_validation,
						)

	@staticmethod
	def _extract_formula(cell: Dict[str, Any]) -> Optional[str]:
		user_entered = cell.get("userEnteredValue") or {}
		formula = user_entered.get("formulaValue")
		if formula:
			return formula.strip()
		return None

	@staticmethod
	def _parse_formula_dependencies(formula: Optional[str], sheet_title: str) -> List[str]:
		if not formula or not formula.startswith("="):
			return []

		dependencies: List[str] = []
		for match in CELL_REF_REGEX.findall(formula):
			ref = match.replace("$", "")
			if "!" in ref:
				sheet_ref, cell_ref = ref.split("!", 1)
				sheet_ref = sheet_ref.strip("'")
			else:
				sheet_ref, cell_ref = sheet_title, ref
			dependencies.append(f"{sheet_ref}!{cell_ref}")

		return sorted(set(dependencies))

	@staticmethod
	def _classify_business_rule(formula: Optional[str]) -> Optional[str]:
		if not formula:
			return None

		upper_formula = formula.upper()
		for category, keywords in BUSINESS_RULE_KEYWORDS.items():
			if any(keyword in upper_formula for keyword in keywords):
				return category
		if upper_formula.startswith("="):
			return "GENERAL_CALCULATION"
		return None

	@staticmethod
	def _extract_effective_value(cell: Dict[str, Any]) -> Any:
		effective = cell.get("effectiveValue") or {}
		if "numberValue" in effective:
			return effective["numberValue"]
		if "stringValue" in effective:
			return effective["stringValue"]
		if "boolValue" in effective:
			return effective["boolValue"]
		if "errorValue" in effective:
			return effective["errorValue"].get("message")
		return cell.get("formattedValue")

	@staticmethod
	def _summarize_data_validation(validation: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
		if not validation:
			return None
		condition = validation.get("condition", {})
		summary = {
			"type": condition.get("type"),
			"strict": validation.get("strict", False),
			"showCustomUi": validation.get("showCustomUi", False),
		}
		values = condition.get("values")
		if values:
			summary["values"] = [v.get("userEnteredValue") for v in values if v.get("userEnteredValue")]
		return summary

	@staticmethod
	def _build_dependency_graph(dependency_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
		graph = nx.DiGraph()
		for cell, deps in dependency_map.items():
			graph.add_node(cell)
			for dep in deps:
				graph.add_edge(dep, cell)
		return {cell: sorted(set(deps)) for cell, deps in dependency_map.items()}

	@staticmethod
	def _detect_cycles(dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
		if not dependency_graph:
			return []
		graph = nx.DiGraph()
		for target, deps in dependency_graph.items():
			graph.add_node(target)
			for dep in deps:
				graph.add_edge(dep, target)
		return [cycle for cycle in nx.simple_cycles(graph)]

	@staticmethod
	def _find_missing_dependencies(
		dependency_map: Dict[str, List[str]],
		raw_values: Dict[str, Dict[str, Any]],
	) -> List[str]:
		known_cells = {
			f"{sheet}!{cell}"
			for sheet, cells in raw_values.items()
			for cell in cells.keys()
		}
		missing: List[str] = []
		for deps in dependency_map.values():
			for dep in deps:
				if dep not in known_cells and dep not in missing:
					missing.append(dep)
		return missing

	def _extract_conditional_formatting(self, api_response: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
		results: Dict[str, List[Dict[str, Any]]] = {}
		for sheet in api_response.get("sheets", []):
			title = sheet.get("properties", {}).get("title", "Sheet1")
			rules: List[Dict[str, Any]] = []
			for idx, rule in enumerate(sheet.get("conditionalFormats", [])):
				summary: Dict[str, Any] = {"index": idx, "ranges": rule.get("ranges", [])}
				if "booleanRule" in rule:
					summary["type"] = "booleanRule"
					summary["condition"] = rule["booleanRule"].get("condition", {}).get("type")
				elif "gradientRule" in rule:
					summary["type"] = "gradientRule"
				else:
					summary["type"] = "unknown"
				rules.append(summary)
			if rules:
				results[title] = rules
		return results

	def _extract_sheet_metadata(
		self,
		api_response: Dict[str, Any],
		sheet_id: str,
		range_name: Optional[str],
		*,
		total_cells: int,
		formula_cells: int,
		missing_dependencies: int,
		last_updated: Optional[str],
		dependency_cycles: List[List[str]],
	) -> Dict[str, Any]:
		spreadsheet_props = api_response.get("properties", {})
		metadata = {
			"sheet_id": sheet_id,
			"range": range_name,
			"spreadsheet_title": spreadsheet_props.get("title"),
			"generated_at": datetime.now(UTC).isoformat(),
			"last_updated": last_updated,
			"sheet_titles": [sheet.get("properties", {}).get("title") for sheet in api_response.get("sheets", [])],
			"total_cells": total_cells,
			"formula_cell_count": formula_cells,
			"missing_dependencies": missing_dependencies,
			"dependency_cycles": dependency_cycles,
		}
		return metadata

	def _lookup_last_updated(self, sheet_id: str) -> Optional[str]:
		if not self.drive_service:
			return None
		try:
			response = self.drive_service.files().get(
				fileId=sheet_id, fields="modifiedTime,lastModifyingUser,owners"
			).execute()
			return response.get("modifiedTime")
		except Exception:  # pragma: no cover - defensive
			LOGGER.debug("Unable to fetch Google Drive metadata for %s", sheet_id, exc_info=True)
			return None

	def _persist_normalized_cache(
		self,
		sheet_id: str,
		range_name: Optional[str],
		context: Dict[str, Any],
	) -> None:
		filename = self._normalized_cache_filename(sheet_id, range_name)
		payload = {
			"sheet_id": sheet_id,
			"range": range_name,
			"generated_at": datetime.now(UTC).isoformat(),
			"metadata": context.get("metadata", {}),
			"cells": context.get("formula_contexts", []),
		}
		with open(filename, "w", encoding="utf-8") as fh:
			json.dump(payload, fh, indent=2)

	def _normalized_cache_filename(self, sheet_id: str, range_name: Optional[str]) -> Path:
		slug_range = self._slugify_range(range_name) if range_name else "entire_sheet"
		return self._formula_cache_dir / f"{sheet_id}_{slug_range}.json"

	@staticmethod
	def _slugify_range(range_name: str) -> str:
		return RANGE_SANITIZE_REGEX.sub("_", range_name)[:120]

	@staticmethod
	def _to_a1(row_index: int, column_index: int) -> str:
		column_label = ""
		col = column_index
		while True:
			col, remainder = divmod(col, 26)
			column_label = chr(ord("A") + remainder) + column_label
			if col == 0:
				break
			col -= 1
		return f"{column_label}{row_index + 1}"

	@staticmethod
	def _empty_context(sheet_id: str, range_name: Optional[str]) -> Dict[str, Any]:
		return {
			"raw_values": {},
			"formulas": {},
			"dependencies": {},
			"business_rules": {},
			"data_validation": {},
			"conditional_formatting": {},
			"metadata": {
				"sheet_id": sheet_id,
				"range": range_name,
				"generated_at": datetime.now(UTC).isoformat(),
				"total_cells": 0,
				"formula_cell_count": 0,
				"missing_dependencies": 0,
				"dependency_cycles": [],
				"sheet_titles": [],
			},
			"missing_dependencies": [],
			"formula_contexts": [],
		}

	# ------------------------------------------------------------------
	# Phase 2: Business Logic Analysis methods

	def classify_formulas_detailed(self, formulas: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
		"""
		Classify formulas using the enhanced FormulaClassifier.
		
		Args:
			formulas: Dict of cell_address -> formula_string
			
		Returns:
			Detailed classifications with categories and confidence
		"""
		classifier = FormulaClassifier()
		return classifier.classify_formulas_batch(formulas)

	def export_dependency_graph(self, dependencies: Dict[str, List[str]], 
							   output_path: str, format: str = 'graphml') -> str:
		"""
		Export dependency graph for visualization.
		
		Args:
			dependencies: Dependency graph adjacency list
			output_path: Base path for output file
			format: Export format ('graphml', 'dot', 'json')
			
		Returns:
			Path to exported file
		"""
		return export_dependency_graph(dependencies, output_path, format)

	def analyze_dependencies(self, dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
		"""
		Analyze dependency graph for insights and issues.
		
		Args:
			dependencies: Dependency graph adjacency list
			
		Returns:
			Analysis results including cycles, components, etc.
		"""
		return analyze_dependency_graph(dependencies)

	def get_business_logic_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Generate summary of business logic from extracted context.
		
		Args:
			context: Context dict from get_comprehensive_sheet_context
			
		Returns:
			Summary with formula categories, cycles, missing deps, etc.
		"""
		formulas = context.get('formulas', {})
		dependencies = context.get('dependencies', {})
		missing_deps = context.get('missing_dependencies', [])
		cycles = context.get('metadata', {}).get('dependency_cycles', [])
		
		# Get detailed classifications
		detailed_classifications = self.classify_formulas_detailed(formulas)
		
		# Count categories
		category_counts = {}
		for classification in detailed_classifications.values():
			category = classification['category']
			category_counts[category] = category_counts.get(category, 0) + 1
		
		# Analyze dependencies
		dep_analysis = self.analyze_dependencies(dependencies)
		
		return {
			'total_formulas': len(formulas),
			'formula_categories': category_counts,
			'missing_dependencies': missing_deps,
			'circular_references': cycles,
			'dependency_analysis': dep_analysis,
			'detailed_classifications': detailed_classifications
		}

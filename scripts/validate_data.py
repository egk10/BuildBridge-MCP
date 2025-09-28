#!/usr/bin/env python3
"""Validate data sources against declared contracts and produce normalized caches."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "src"))

from connectors.google_sheets_connector import GoogleSheetsConnector  # noqa: E402
from utils.google_sheet_parser import ParsedSheet, parse_sheet  # noqa: E402

CONFIG_PATH = ROOT_DIR / "config" / "credentials.json"
CONTRACT_PATH = ROOT_DIR / "config" / "contracts" / "google_project_tabs.json"
NORMALIZED_DIR = ROOT_DIR / "cache" / "normalized"


class ValidationError(Exception):
    pass


def load_config() -> Dict:
    with open(CONFIG_PATH) as fh:
        return json.load(fh)


def load_contract() -> Dict:
    with open(CONTRACT_PATH) as fh:
        return json.load(fh)


def resolve_explicit_tabs(available: List[str], candidates: List[str]) -> List[str]:
    available_lower = {tab.lower(): tab for tab in available}
    resolved: List[str] = []
    for candidate in candidates:
        resolved_name = available_lower.get(candidate.lower())
        if resolved_name and resolved_name not in resolved:
            resolved.append(resolved_name)
    return resolved


def match_tabs(available: List[str], match_cfg: Dict[str, str]) -> List[str]:
    matched: List[str] = []
    if not match_cfg:
        return matched

    match_type = (match_cfg.get("type") or "").lower()
    pattern = match_cfg.get("pattern") or match_cfg.get("value")
    if not match_type or not pattern:
        return matched

    if match_type == "regex":
        regex = re.compile(pattern, re.IGNORECASE)
        for tab in available:
            if regex.search(tab) and tab not in matched:
                matched.append(tab)
    elif match_type == "startswith":
        prefix = pattern.lower()
        for tab in available:
            if tab.lower().startswith(prefix) and tab not in matched:
                matched.append(tab)
    elif match_type == "contains":
        needle = pattern.lower()
        for tab in available:
            if needle in tab.lower() and tab not in matched:
                matched.append(tab)

    return matched


def validate_tab(contract: Dict, parsed: ParsedSheet) -> Dict:
    values: Dict[str, Optional[str]] = {}
    presence: Dict[str, bool] = {}
    errors: List[str] = []

    for field in contract.get("fields", []):
        field_type = field.get("type", "value").lower()
        key = field["key"]
        labels = field.get("labels", [])
        required = field.get("required", False)

        if field_type == "value":
            value = parsed.get_value(labels)
            if required and (value is None or value == ""):
                errors.append(f"Missing required value for '{key}' (labels: {labels})")
            values[key] = value
        elif field_type == "presence":
            present = parsed.has_label(labels)
            if required and not present:
                errors.append(f"Missing required label for '{key}' (labels: {labels})")
            presence[key] = present
        else:
            errors.append(f"Unknown field type '{field_type}' for key '{key}'")

    return {"values": values, "presence": presence, "errors": errors}


def validate_project(connector: GoogleSheetsConnector, contract: Dict, project_key: str, sheet_id: str) -> Dict:
    available_tabs = connector.list_available_sheets(sheet_id)
    project_result = {
        "project_key": project_key,
        "sheet_id": sheet_id,
        "tabs": [],
        "errors": []
    }

    for tab_contract in contract.get("tab_contracts", []):
        tab_id = tab_contract["id"]
        tab_required = tab_contract.get("required", False)
        allow_multiple = tab_contract.get("allow_multiple", False)

        matched_tabs: List[str] = []
        matched_tabs.extend(resolve_explicit_tabs(available_tabs, tab_contract.get("tab_names", [])))
        matched_tabs.extend(match_tabs(available_tabs, tab_contract.get("match", {})))

        seen = set()
        ordered_matches: List[str] = []
        for tab in available_tabs:
            if tab in matched_tabs and tab not in seen:
                ordered_matches.append(tab)
                seen.add(tab)

        if not ordered_matches:
            message = f"Tab '{tab_id}' not found for project '{project_key}'"
            if tab_required:
                project_result["errors"].append(message)
            else:
                project_result.setdefault("warnings", []).append(message)
            continue

        tabs_to_process = ordered_matches if allow_multiple else ordered_matches[:1]

        for actual_tab_name in tabs_to_process:
            df = connector.read_sheet(sheet_id, f"'{actual_tab_name}'!A1:Z200")
            df = df.replace("\u00a0", " ", regex=True)
            parsed = parse_sheet(df)
            tab_result = validate_tab(tab_contract, parsed)

            project_result["tabs"].append({
                "contract_id": tab_id,
                "source_tab": actual_tab_name,
                **tab_result,
                "raw_row_count": len(parsed.raw_rows)
            })

            project_result["errors"].extend(tab_result["errors"])

    return project_result


def write_normalized_cache(result: Dict) -> None:
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "project_key": result["project_key"],
        "sheet_id": result["sheet_id"],
        "generated_at": datetime.now(UTC).isoformat(),
        "tabs": [
            {
                "contract_id": tab_res["contract_id"],
                "source_tab": tab_res["source_tab"],
                "values": tab_res["values"],
                "presence": tab_res["presence"],
                "raw_row_count": tab_res["raw_row_count"]
            }
            for tab_res in result["tabs"]
        ]
    }
    output_path = NORMALIZED_DIR / f"{result['project_key']}.json"
    with open(output_path, "w") as fh:
        json.dump(output, fh, indent=2)


def run_validation(project_filter: Optional[List[str]] = None) -> int:
    config = load_config()
    contract = load_contract()

    connector = GoogleSheetsConnector(config)
    projects = config.get("google_sheets", {}).get("projects", {})

    failures = 0
    results = []

    for project_key, sheet_id in projects.items():
        if project_filter and project_key not in project_filter:
            continue

        result = validate_project(connector, contract, project_key, sheet_id)
        results.append(result)
        if result["errors"]:
            failures += 1
            status = "FAIL"
        else:
            status = "PASS"

        print(f"[{status}] {project_key}")
        for error in result["errors"]:
            print(f"  - ERROR: {error}")
        for warning in result.get("warnings", []):
            print(f"  - WARNING: {warning}")

        write_normalized_cache(result)

    report_path = NORMALIZED_DIR / "validation_report.json"
    with open(report_path, "w") as fh:
        json.dump({"generated_at": datetime.now(UTC).isoformat(), "results": results}, fh, indent=2)

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate BuildBridge data sources")
    parser.add_argument("--project", action="append", help="Project key to validate (can be specified multiple times)")
    args = parser.parse_args()

    failures = run_validation(args.project)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

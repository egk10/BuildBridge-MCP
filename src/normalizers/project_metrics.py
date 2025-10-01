"""Utilities for building cached project metric summaries from manifest outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

__all__ = [
    "Metric",
    "DEFAULT_CACHE_DIR",
    "DEFAULT_OUTPUT_PATH",
    "iter_project_cache_files",
    "build_project_metrics",
    "write_project_metrics_summary",
]

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = ROOT_DIR / "cache" / "normalized"
DEFAULT_OUTPUT_PATH = DEFAULT_CACHE_DIR / "project_metrics.json"


@dataclass
class Metric:
    key: str
    raw: Optional[str]
    value: Optional[float | int]
    source_tab: Optional[str]

    def as_dict(self) -> Dict[str, Optional[float | int | str]]:
        return {
            "raw": self.raw,
            "value": self.value,
            "source_tab": self.source_tab,
        }


def iter_project_cache_files(cache_dir: Path) -> Iterable[Path]:
    for path in cache_dir.glob("*.json"):
        if path.name in {"validation_report.json", "project_metrics.json"}:
            continue
        yield path


def _parse_numeric(value: Optional[str]) -> Optional[float | int]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]
        negative = True

    cleaned = cleaned.replace(",", "")

    if cleaned.endswith("%"):
        try:
            number = float(cleaned[:-1]) / 100
            return -number if negative else number
        except ValueError:
            return None

    try:
        number = float(cleaned)
    except ValueError:
        return None

    if negative:
        number *= -1

    if number.is_integer():
        return int(number)
    return number


def _collect_metrics(project_cache: Dict[str, object]) -> Dict[str, Metric]:
    metrics: Dict[str, Metric] = {}

    for tab in project_cache.get("tabs", []):
        if not isinstance(tab, dict):
            continue
        contract_id = tab.get("contract_id")
        values = tab.get("values") or {}
        if not isinstance(values, dict):
            continue

        if contract_id == "project_info":
            for key in [
                "building_area_metric",
                "building_area_imperial",
                "functional_units",
                "parking_stalls",
            ]:
                raw = values.get(key)
                metrics[key] = Metric(
                    key=key,
                    raw=raw,
                    value=_parse_numeric(raw if isinstance(raw, str) else None),
                    source_tab=tab.get("source_tab"),
                )

        if contract_id == "suite_count":
            raw = values.get("total_suites")
            metrics["total_suites"] = Metric(
                key="total_suites",
                raw=raw,
                value=_parse_numeric(raw if isinstance(raw, str) else None),
                source_tab=tab.get("source_tab"),
            )

        if contract_id == "gca_stats":
            for key in [
                "parking_below_grade",
                "parking_above_grade",
                "parking_total",
            ]:
                raw = values.get(key)
                metrics[key] = Metric(
                    key=key,
                    raw=raw,
                    value=_parse_numeric(raw if isinstance(raw, str) else None),
                    source_tab=tab.get("source_tab"),
                )

    for key in [
        "building_area_metric",
        "building_area_imperial",
        "functional_units",
        "total_suites",
        "parking_stalls",
        "parking_below_grade",
        "parking_above_grade",
        "parking_total",
    ]:
        metrics.setdefault(
            key,
            Metric(key=key, raw=None, value=None, source_tab=None),
        )

    return metrics


def build_project_metrics(cache_dir: Path) -> Dict[str, Dict[str, Metric]]:
    aggregated: Dict[str, Dict[str, Metric]] = {}
    if not cache_dir.exists():
        return aggregated
    for cache_path in iter_project_cache_files(cache_dir):
        try:
            with cache_path.open() as fh:
                project_cache = json.load(fh)
        except Exception:
            continue
        project_key = project_cache.get("project_key") or cache_path.stem
        if not project_key:
            continue
        aggregated[str(project_key)] = _collect_metrics(project_cache)
    return aggregated


def _build_metrics_payload(metrics: Dict[str, Dict[str, Metric]]) -> Dict[str, object]:
    projects = []
    for project_key, project_metrics in sorted(metrics.items()):
        projects.append(
            {
                "project_key": project_key,
                "metrics": {key: metric.as_dict() for key, metric in sorted(project_metrics.items())},
            }
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "projects": projects,
    }


def write_project_metrics_summary(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Dict[str, object]:
    metrics = build_project_metrics(cache_dir)
    payload = _build_metrics_payload(metrics)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as fh:
        json.dump(payload, fh, indent=2)
    return payload
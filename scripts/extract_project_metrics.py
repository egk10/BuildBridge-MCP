#!/usr/bin/env python3
"""Aggregate key project metrics from normalized validation caches."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "cache" / "normalized"
OUTPUT_PATH = NORMALIZED_DIR / "project_metrics.json"


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


def _iter_project_cache_files() -> Iterable[Path]:
    for path in NORMALIZED_DIR.glob("*.json"):
        if path.name in {"validation_report.json", "project_metrics.json"}:
            continue
        yield path


def _parse_numeric(value: Optional[str]) -> Optional[float | int]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    # Handle accounting negatives (e.g., "(123)").
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
        return int(number)  # type: ignore[return-value]
    return number


def _collect_metrics(project_cache: Dict) -> Dict[str, Metric]:
    metrics: Dict[str, Metric] = {}

    for tab in project_cache.get("tabs", []):
        contract_id = tab.get("contract_id")
        values = tab.get("values", {}) or {}

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
                    value=_parse_numeric(raw),
                    source_tab=tab.get("source_tab"),
                )

        if contract_id == "suite_count":
            raw = values.get("total_suites")
            metrics["total_suites"] = Metric(
                key="total_suites",
                raw=raw,
                value=_parse_numeric(raw),
                source_tab=tab.get("source_tab"),
            )

    # Ensure keys exist even if absent in source data.
    for key in [
        "building_area_metric",
        "building_area_imperial",
        "functional_units",
        "total_suites",
        "parking_stalls",
    ]:
        metrics.setdefault(
            key,
            Metric(key=key, raw=None, value=None, source_tab=None),
        )

    return metrics


def build_project_metrics() -> Dict[str, Dict[str, Metric]]:
    aggregated: Dict[str, Dict[str, Metric]] = {}
    for cache_path in _iter_project_cache_files():
        with open(cache_path) as fh:
            project_cache = json.load(fh)
        project_key = project_cache.get("project_key") or cache_path.stem
        aggregated[project_key] = _collect_metrics(project_cache)
    return aggregated


def write_metrics(metrics: Dict[str, Dict[str, Metric]]) -> None:
    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "projects": [],
    }
    for project_key, project_metrics in sorted(metrics.items()):
        output["projects"].append(
            {
                "project_key": project_key,
                "metrics": {
                    key: metric.as_dict() for key, metric in sorted(project_metrics.items())
                },
            }
        )

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(output, fh, indent=2)


def main() -> None:
    metrics = build_project_metrics()
    write_metrics(metrics)


if __name__ == "__main__":
    main()

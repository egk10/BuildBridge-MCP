#!/usr/bin/env python3
"""Simulate the `/process` response for User Input 1 using manifest caches."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

CACHE_DIR = PROJECT_ROOT / "cache" / "normalized"
METRICS_PATH = CACHE_DIR / "project_metrics.json"

USER_PROMPT = (
    "Hi BuildBridge! I need to analyze cost data across my three active projects: "
    "72 Perth, 17175 Yonge St, and Azure Road. Can you show me a summary of all three projects first?"
)


def _load_metrics() -> Dict[str, Dict[str, Dict[str, str]]]:
    if not METRICS_PATH.exists():
        raise FileNotFoundError(
            "Project metrics cache not found. Run scripts/refresh_manifest_local.py first."
        )
    payload = json.loads(METRICS_PATH.read_text())
    return {
        entry["project_key"].lower(): entry["metrics"]
        for entry in payload.get("projects", [])
        if entry.get("project_key")
    }


def _load_project_payload(project_id: str) -> Dict:
    cache_path = CACHE_DIR / f"{project_id}.json"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Normalized cache for '{project_id}' missing at {cache_path}. "
            "Run the refresh script to generate it."
        )
    return json.loads(cache_path.read_text())


def _format_currency(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def _format_area(value: float | int | None, unit: str = "sf") -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f} {unit}"


def _extract_metric(metrics: Dict[str, Dict[str, str]], key: str) -> float | int | None:
    metric = metrics.get(key)
    if not metric:
        return None
    value = metric.get("value")
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _summarize_project(project_id: str, metrics_map: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    payload = _load_project_payload(project_id)
    project_meta = payload.get("project", {})
    metrics = metrics_map.get(project_id.lower(), {})

    name = project_meta.get("Project_Name") or project_meta.get("Project_ID", project_id)
    location = project_meta.get("Location", "Unknown Location")
    budget = project_meta.get("Total_Budget")
    if isinstance(budget, str):
        try:
            budget = float(budget.replace(",", ""))
        except ValueError:
            budget = None

    area_sf = _extract_metric(metrics, "building_area_imperial")
    area_m2 = _extract_metric(metrics, "building_area_metric")
    units = _extract_metric(metrics, "functional_units")
    parking = _extract_metric(metrics, "parking_total") or _extract_metric(metrics, "parking_stalls")

    lines = [f"📊 **{name}**", f"- Location: {location}"]
    lines.append(f"- Total Budget: {_format_currency(budget)}")
    lines.append(f"- Gross Construction Area: {_format_area(area_sf)} ({_format_area(area_m2, 'm²')})")
    if units is not None:
        lines.append(f"- Functional Units: {int(units):,}")
    if parking is not None:
        lines.append(f"- Parking Stalls: {int(parking):,}")

    return "\n".join(lines)


def build_response(project_ids: List[str]) -> str:
    metrics_map = _load_metrics()
    sections = ["🏗️ **BuildBridge Assistant**: Here's the latest summary pulled from the manifest cache."]
    for project_id in project_ids:
        sections.append("")
        sections.append(_summarize_project(project_id, metrics_map))
    sections.append("")
    sections.append("Let me know if you'd like deeper cost breakdowns or trend comparisons next.")
    return "\n".join(sections)


def main() -> None:
    project_ids = ["72_perth", "17175_yonge_st", "azure_road"]
    response = build_response(project_ids)

    print("=== User Input 1 ===")
    print(USER_PROMPT)
    print("\n=== Simulated /process Response ===")
    print(response)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "src"))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from connectors.google_sheets_connector import GoogleSheetsConnector  # noqa: E402
from parsers.google_sheet_manifest_parsers import ParserResult  # noqa: E402


@pytest.fixture()
def normalized_paths():
    root = Path(__file__).resolve().parents[1]
    normalized_dir = root / "cache" / "normalized"
    project_path = normalized_dir / "17175_yonge_st.json"
    metrics_path = normalized_dir / "project_metrics.json"

    if project_path.exists():
        project_path.unlink()
    if metrics_path.exists():
        metrics_path.unlink()

    yield project_path, metrics_path

    if project_path.exists():
        project_path.unlink()
    if metrics_path.exists():
        metrics_path.unlink()


def test_refresh_manifest_project_creates_cache_and_metrics(monkeypatch, normalized_paths):
    project_path, metrics_path = normalized_paths

    config = {
        "local_mode": True,
        "project_manifest_file": "config/project_manifest.json",
        "google_sheets": {"projects": {"17175_yonge_st": "dummy-sheet"}},
    }

    connector = GoogleSheetsConnector(config)

    sample_tabs = [
        {
            "contract_id": "project_info",
            "source_tab": "Project Summary",
            "values": {
                "building_area_metric": "10,000",
                "building_area_imperial": "107,639",
                "functional_units": "208",
                "parking_stalls": "150",
            },
        },
        {
            "contract_id": "suite_count",
            "source_tab": "Project Summary",
            "values": {"total_suites": "208"},
        },
        {
            "contract_id": "gca_stats",
            "source_tab": "GCA Stats",
            "values": {
                "parking_below_grade": "120",
                "parking_above_grade": "30",
                "parking_total": "150",
            },
        },
    ]

    sample_project = {
        "Project_ID": "17175_yonge_st",
        "Total_Budget": 5_000_000,
    }

    sample_result = ParserResult(tabs=sample_tabs, project=sample_project)

    monkeypatch.setattr(
        connector,
        "fetch_project_manifest_data",
        lambda project_id, force_refresh=False: sample_result,
    )

    payload = connector.refresh_manifest_project("17175_yonge_st", force_refresh=True)

    assert payload["project_key"] == "17175_yonge_st"
    assert project_path.exists()

    with project_path.open() as fh:
        cached = json.load(fh)

    assert cached["project"]["Total_Budget"] == 5_000_000
    assert any(tab["contract_id"] == "project_info" for tab in cached["tabs"])

    assert metrics_path.exists()
    with metrics_path.open() as fh:
        metrics_payload = json.load(fh)

    entry = next(
        item for item in metrics_payload["projects"] if item["project_key"] == "17175_yonge_st"
    )
    assert entry["metrics"]["building_area_metric"]["raw"] == "10,000"
    assert entry["metrics"]["parking_total"]["value"] == 150
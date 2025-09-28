"""Tests for the enhanced Google Sheets connector formula extraction."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from connectors.enhanced_google_sheets_connector import (  # type: ignore
    EnhancedGoogleSheetsConnector,
)


SAMPLE_RESPONSE = {
    "properties": {"title": "Sample Workbook"},
    "sheets": [
        {
            "properties": {"title": "Main"},
            "data": [
                {
                    "startRow": 0,
                    "startColumn": 0,
                    "rowData": [
                        {
                            "values": [
                                {
                                    "formattedValue": "10",
                                    "effectiveValue": {"numberValue": 10},
                                },
                                {
                                    "formattedValue": "20",
                                    "userEnteredValue": {"formulaValue": "=A1*2"},
                                    "effectiveValue": {"numberValue": 20},
                                },
                            ]
                        },
                        {
                            "values": [
                                {
                                    "formattedValue": "Option",
                                    "userEnteredValue": {"stringValue": "Option"},
                                    "dataValidation": {
                                        "condition": {
                                            "type": "ONE_OF_LIST",
                                            "values": [{"userEnteredValue": "Option"}],
                                        },
                                        "strict": True,
                                    },
                                },
                                {
                                    "formattedValue": "30",
                                    "userEnteredValue": {"formulaValue": "=SUM(A1,B1)"},
                                    "effectiveValue": {"numberValue": 30},
                                },
                            ]
                        },
                    ],
                }
            ],
            "conditionalFormats": [
                {
                    "ranges": [
                        {
                            "startRowIndex": 0,
                            "endRowIndex": 2,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }
                    ],
                    "booleanRule": {
                        "condition": {"type": "TEXT_CONTAINS"},
                        "format": {"textFormat": {"bold": True}},
                    },
                }
            ],
        }
    ],
}


def test_comprehensive_context_extraction(tmp_path):
    config = {
        "local_mode": True,
        "google_sheets": {},
        "formula_cache_dir": str(tmp_path),
    }

    connector = EnhancedGoogleSheetsConnector(config)
    connector.local_mode = False  # allow execution path
    connector._fetch_sheet_response = lambda *args, **kwargs: SAMPLE_RESPONSE  # type: ignore
    connector._lookup_last_updated = lambda sheet_id: "2025-09-26T12:00:00Z"  # type: ignore

    context = connector.get_comprehensive_sheet_context("sheet123", range_name="Main!A1:B2")

    assert context["formulas"]["Main"]["B1"] == "=A1*2"
    assert "Main!A1" in context["dependencies"]["Main!B1"]
    assert context["business_rules"]["Main!B1"] == "GENERAL_CALCULATION"
    assert context["data_validation"]["Main!A2"]["type"] == "ONE_OF_LIST"
    assert context["metadata"]["formula_cell_count"] == 2
    assert context["conditional_formatting"]["Main"][0]["type"] == "booleanRule"

    cache_files = list(Path(tmp_path).glob("*.json"))
    assert len(cache_files) == 1

    payload = json.loads(cache_files[0].read_text())
    assert payload["metadata"]["sheet_id"] == "sheet123"
    assert payload["cells"][0]["provenance"]["sheet_title"] == "Main"
#!/usr/bin/env python3
"""Command-line helper for validating formula extraction on Google Sheets projects."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.connectors.enhanced_google_sheets_connector import EnhancedGoogleSheetsConnector
from src.secure_config import SecureConfig


def load_config() -> dict:
    load_dotenv(ROOT_DIR / ".env", override=True)
    return SecureConfig().build_legacy_config()


def test_sheet_extraction(sheet_key: str, sheet_id: str) -> bool:
    config = load_config()
    connector = EnhancedGoogleSheetsConnector(config)

    print(f"Testing formula extraction for {sheet_key} (ID: {sheet_id})...")

    try:
        context = connector.get_comprehensive_sheet_context(sheet_id, range_name=None)

        metadata = context.get("metadata", {})
        total_cells = metadata.get("total_cells", 0)
        formula_cells = metadata.get("formula_cell_count", 0)
        missing_deps = len(context.get("missing_dependencies", []))
        cycles = metadata.get("dependency_cycles", [])

        success_rate = (total_cells - missing_deps) / total_cells if total_cells else 0

        print(f"  Total cells examined: {total_cells}")
        print(f"  Formula cells found: {formula_cells}")
        print(f"  Missing dependencies: {missing_deps}")
        print(f"  Circular references: {len(cycles)}")
        print(f"  Successful extraction rate: {success_rate:.2%}")

        cache_files = list(connector._formula_cache_dir.glob(f"{sheet_id}_*.json"))
        cache_present = bool(cache_files)
        print(f"  Normalized cache created: {cache_present}")
        if cache_files:
            print(f"  Cache file: {cache_files[0]}")

        extraction_success = success_rate >= 0.95 and cache_present
        print(f"  Phase 1 exit criteria met: {extraction_success}")

        return extraction_success

    except Exception as exc:  # pragma: no cover - interactive CLI feedback
        print(f"  ERROR: {exc}")
        return False


def main() -> None:
    config = load_config()
    projects = config.get("google_sheets", {}).get("projects", {})

    print("Formula Extraction Pilot Test")
    print("=" * 40)

    if not projects:
        print("No Google Sheets projects configured. Update your .env file first.")
        return

    results: dict[str, bool] = {}
    for project_key, sheet_id in projects.items():
        results[project_key] = test_sheet_extraction(project_key, sheet_id)
        print()

    print("Summary:")
    for project, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {project}: {status}")

    overall_success = all(results.values()) if results else False
    print(f"\nOverall: {'PASS' if overall_success else 'FAIL'}")

    if overall_success:
        print("Phase 1 exit criteria satisfied for all pilot sheets!")
    else:
        print("Some pilot sheets failed Phase 1 criteria.")
if __name__ == "__main__":
    main()

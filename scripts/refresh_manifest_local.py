#!/usr/bin/env python3
"""Refresh manifest caches using local CSV sources for offline development."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd  # noqa: F401  # Ensures pandas dependency for connector local mode

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from connectors.google_sheets_connector import GoogleSheetsConnector  # type: ignore  # noqa: E402

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "config" / "project_manifest.json"


def _build_connector_config(project_ids: Iterable[str], manifest_path: Path) -> dict:
    """Build a minimal connector config for local manifest refresh."""

    projects_mapping = {project_id: f"local-{project_id}" for project_id in project_ids}

    return {
        "local_mode": True,
        "project_manifest_file": str(manifest_path.relative_to(PROJECT_ROOT)),
        "google_sheets": {"projects": projects_mapping},
    }


def refresh_projects(project_ids: List[str], force: bool) -> None:
    """Refresh manifest caches for the supplied project IDs."""

    manifest_path = DEFAULT_MANIFEST_PATH
    config = _build_connector_config(project_ids, manifest_path)
    connector = GoogleSheetsConnector(config)
    connector.refresh_manifest_projects(project_ids=project_ids, force_refresh=force)

    summary = connector.rebuild_project_metrics_summary()
    refreshed = ", ".join(project_ids)
    print(f"✅ Refreshed manifest cache for: {refreshed}")
    print(f"📄 Metrics summary now includes {len(summary.get('projects', []))} project entries")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "projects",
        nargs="*",
        help="Optional project IDs to refresh (defaults to all configured projects)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh by bypassing any existing cache",
    )
    args = parser.parse_args()

    manifest_path = DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    manifest_data = json.loads(manifest_path.read_text())
    project_ids = args.projects or list(manifest_data.keys())

    if not project_ids:
        raise SystemExit("No project IDs provided and manifest is empty")

    refresh_projects(project_ids, force=args.force)


if __name__ == "__main__":
    main()

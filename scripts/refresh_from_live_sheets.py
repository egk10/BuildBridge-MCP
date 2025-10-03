#!/usr/bin/env python3
"""Refresh manifest caches from LIVE Google Sheets (not CSV files)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from connectors.google_sheets_connector import GoogleSheetsConnector
from secure_config import SecureConfig

def main():
    """Refresh cache from live Google Sheets."""
    
    print("🔄 Refreshing cache from LIVE Google Sheets (not CSV files)...")
    print("=" * 60)
    
    # Load configuration with Google Sheets credentials
    secure_config = SecureConfig()
    config = secure_config.build_legacy_config()
    
    # Ensure local_mode is FALSE to read from live sheets
    if 'local_mode' in config:
        config['local_mode'] = False
    
    google_sheets_config = config.get('google_sheets', {})
    projects = google_sheets_config.get('projects', {})
    
    if not projects:
        print("❌ No projects configured in google_sheets.projects")
        return 1
    
    print(f"📊 Found {len(projects)} projects: {list(projects.keys())}")
    print()
    
    # Create connector with live mode
    connector = GoogleSheetsConnector(config)
    
    # Refresh each project from live sheets
    project_ids = list(projects.keys())
    
    print("🔄 Refreshing from Google Sheets API...")
    connector.refresh_manifest_projects(project_ids=project_ids, force_refresh=True)
    
    print()
    print("📊 Rebuilding metrics summary...")
    summary = connector.rebuild_project_metrics_summary()
    
    print()
    print("=" * 60)
    print(f"✅ Successfully refreshed {len(project_ids)} projects from live Google Sheets")
    print(f"📄 Metrics summary now includes {len(summary.get('projects', []))} project entries")
    print()
    
    # Show what was loaded
    cache_dir = PROJECT_ROOT / 'cache' / 'normalized'
    for project_id in project_ids:
        cache_file = cache_dir / f"{project_id}.json"
        if cache_file.exists():
            import json
            with open(cache_file, 'r') as f:
                data = json.load(f)
                project_data = data.get('project', {})
                print(f"  {project_id}:")
                print(f"    Name: {project_data.get('Project_Name', 'N/A')}")
                print(f"    Client: {project_data.get('Client', 'N/A')}")
                print(f"    Location: {project_data.get('Location', 'N/A')}")
    
    print()
    print("🎉 Done! Cache refreshed from live Google Sheets.")
    print("   Restart your server to see the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Interactive helper for managing Google Sheets projects in BuildBridge-MCP.

Projects and sheet metadata are persisted to the workspace `.env` file so that
the secure configuration system can surface them automatically at runtime.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import dotenv_values, load_dotenv, set_key, unset_key
from src.secure_config import SecureConfig

PROJECT_PREFIX = "GOOGLE_SHEETS_PROJECT_"
CONFIG_PREFIX = "GOOGLE_SHEETS_CONFIG_"
ENV_FILENAME = ".env"
STANDARD_SHEETS: Tuple[Tuple[str, str], ...] = (
    ("project_summary", "Project Summary"),
    ("exec_summary", "Exec Summary"),
    ("project_info", "Project Info"),
    ("gca_stats", "GCA Stats"),
    ("budget_tracking", "Budget Tracking"),
    ("schedule", "Schedule"),
    ("resources", "Resources"),
    ("safety_incidents", "Safety Incidents"),
    ("subcontractors", "Subcontractors"),
    ("materials", "Materials"),
    ("permits", "Permits"),
    ("quality_control", "Quality Control"),
)

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ENV_FILENAME
ENV_TEMPLATE_PATH = SCRIPT_DIR / f"{ENV_FILENAME}.template"


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def ensure_env_file() -> bool:
    """Ensure that the `.env` file exists before attempting modifications."""

    if ENV_PATH.exists():
        return True

    if ENV_TEMPLATE_PATH.exists():
        ENV_PATH.write_text(ENV_TEMPLATE_PATH.read_text(), encoding="utf-8")
        print(f"⚠️  Created {ENV_PATH} from template. Review and update values before continuing.")
        return True

    print(f"❌ {ENV_PATH} not found and no template available. Create the file before proceeding.")
    return False


def load_env_values() -> Dict[str, str]:
    """Load current environment values from the `.env` file."""

    if not ENV_PATH.exists():
        return {}
    return dotenv_values(str(ENV_PATH))


def slugify_env_token(token: str) -> str:
    cleaned = re.sub(r"[^0-9A-Z]+", "_", token.upper()).strip("_")
    return cleaned or "PROJECT"


def determine_project_slot(project_key: str, env_values: Dict[str, str]) -> str:
    for env_key, value in env_values.items():
        if env_key.startswith(PROJECT_PREFIX) and env_key.endswith("_NAME") and value == project_key:
            return env_key[len(PROJECT_PREFIX) : -len("_NAME")]

    candidate_slots: List[int] = []
    for env_key in env_values:
        if env_key.startswith(PROJECT_PREFIX) and env_key.endswith("_ID"):
            slot = env_key[len(PROJECT_PREFIX) : -len("_ID")]
            if slot.isdigit():
                candidate_slots.append(int(slot))

    next_slot = max(candidate_slots, default=0) + 1
    return str(next_slot)


def set_env_var(key: str, value: str) -> None:
    set_key(str(ENV_PATH), key, value, quote_mode="never")


def remove_env_var(key: str) -> None:
    unset_key(str(ENV_PATH), key)


def project_env_keys(slot: str) -> Tuple[str, str]:
    return (
        f"{PROJECT_PREFIX}{slot}_NAME",
        f"{PROJECT_PREFIX}{slot}_ID",
    )


def sheet_env_base(project_key: str, sheet_key: str) -> str:
    base = slugify_env_token(f"{project_key}_{sheet_key}")
    return f"{CONFIG_PREFIX}{base}"


def sheet_env_keys(project_key: str, sheet_key: str) -> Tuple[str, str]:
    base = sheet_env_base(project_key, sheet_key)
    return f"{base}_SHEET_ID", f"{base}_RANGE"


def refresh_secure_config() -> Dict[str, object]:
    load_dotenv(str(ENV_PATH), override=True)
    return SecureConfig().build_legacy_config()


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def validate_sheet_access(sheet_id: str) -> Tuple[bool, str]:
    if not sheet_id or not sheet_id.strip():
        return False, "Sheet ID cannot be empty"
    if len(sheet_id) < 20:
        return False, "Sheet ID appears too short (expect ~40+ characters)"
    if not re.match(r"^[a-zA-Z0-9_-]+$", sheet_id):
        return False, "Sheet ID contains invalid characters"
    return True, "Sheet ID format appears valid"


def load_current_projects(config: Dict[str, object]) -> Dict[str, str]:
    sheets_config = config.get("google_sheets", {})
    return sheets_config.get("projects", {})  # type: ignore[return-value]


def ensure_standard_sheets(project_key: str) -> int:
    created = 0
    for sheet_key, sheet_name in STANDARD_SHEETS:
        sid_key, range_key = sheet_env_keys(project_key, sheet_key)
        env_values = load_env_values()
        if sid_key in env_values and range_key in env_values:
            continue
        set_env_var(sid_key, f"projects.{project_key}")
        set_env_var(range_key, f"{sheet_name}!A1:Z1000")
        print(f"  ✅ {project_key}.{sheet_key} -> {sheet_name}")
        created += 1
    return created


def remove_standard_sheets(project_key: str) -> int:
    removed = 0
    env_values = load_env_values()
    for sheet_key, _ in STANDARD_SHEETS:
        sid_key, range_key = sheet_env_keys(project_key, sheet_key)
        if sid_key in env_values:
            remove_env_var(sid_key)
            removed += 1
        if range_key in env_values:
            remove_env_var(range_key)
    return removed


def add_project() -> bool:
    print("🏗️  BuildBridge-MCP Project Addition Tool")
    print("=" * 50)

    if not ensure_env_file():
        return False

    config = refresh_secure_config()
    projects = load_current_projects(config)

    print("\n📝 Enter project details:")
    project_name = input("Project name (e.g., 'downtown_toronto'): ").strip()
    if not project_name:
        print("❌ Project name cannot be empty")
        return False

    project_key = project_name.lower().replace(" ", "_").replace("-", "_")

    sheet_id = input("Google Sheet ID: ").strip()
    valid, message = validate_sheet_access(sheet_id)
    if not valid:
        print(f"❌ {message}")
        return False

    if project_key in projects:
        overwrite = input(
            f"⚠️  Project '{project_key}' already exists. Overwrite environment entry? (y/N): "
        ).strip().lower()
        if overwrite != "y":
            print("❌ Operation cancelled")
            return False

    env_values = load_env_values()
    slot = determine_project_slot(project_key, env_values)
    name_key, id_key = project_env_keys(slot)

    set_env_var(name_key, project_key)
    set_env_var(id_key, sheet_id)

    print(f"\n📊 Ensuring standard sheet configurations for '{project_key}':")
    created = ensure_standard_sheets(project_key)

    refresh_secure_config()

    print("\n🎉 Project configuration updated!")
    print(f"   Slot: {slot}")
    print(f"   Project key: {project_key}")
    print(f"   Sheet ID: {sheet_id}")
    print(f"   Added or updated {created} sheet configuration entries")

    if input("\n🧪 Test the new project configuration? (y/N): ").strip().lower() == "y":
        print("\n🧪 Testing configuration...")
        test_project_config(project_key)

    return True


def list_projects() -> None:
    if not ensure_env_file():
        return

    config = refresh_secure_config()
    projects = load_current_projects(config)
    if not projects:
        print("❌ No projects configured")
        return

    print(f"✅ Found {len(projects)} projects\n")
    env_values = load_env_values()
    for key, sheet_id in sorted(projects.items()):
        print(f"📁 {key}")
        print(f"   Sheet ID: {sheet_id}")
        associated = []
        for sheet_key, sheet_name in STANDARD_SHEETS:
            sid_key, _ = sheet_env_keys(key, sheet_key)
            if sid_key in env_values:
                associated.append(sheet_name)
        if associated:
            print(f"   Sheets configured: {', '.join(sorted(set(associated)))}")
        else:
            print("   Sheets configured: None")
        print()

    print("💡 Tip: Use complement option to add missing standard sheets.")


def select_project(projects: Dict[str, str]) -> Optional[str]:
    ordered = sorted(projects.keys())
    for idx, key in enumerate(ordered, 1):
        print(f"  {idx}. {key}")
    choice = input("\nEnter project number: ").strip()
    try:
        return ordered[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid selection")
        return None


def complement_project() -> bool:
    if not ensure_env_file():
        return False

    config = refresh_secure_config()
    projects = load_current_projects(config)
    if not projects:
        print("❌ No projects configured")
        return False

    print("🏗️  Select project to complement:")
    project_key = select_project(projects)
    if not project_key:
        return False

    env_values = load_env_values()
    missing: List[Tuple[str, str]] = []
    for sheet_key, sheet_name in STANDARD_SHEETS:
        sid_key, range_key = sheet_env_keys(project_key, sheet_key)
        if sid_key not in env_values or range_key not in env_values:
            missing.append((sheet_key, sheet_name))

    if not missing:
        print(f"✅ Project '{project_key}' already has all standard sheets configured")
        return True

    print(f"\n📊 Adding {len(missing)} missing sheets to '{project_key}':")
    for sheet_key, sheet_name in missing:
        sid_key, range_key = sheet_env_keys(project_key, sheet_key)
        set_env_var(sid_key, f"projects.{project_key}")
        set_env_var(range_key, f"{sheet_name}!A1:Z1000")
        print(f"  ✅ {sheet_key} -> {sheet_name}")

    refresh_secure_config()
    print(f"\n🎉 Added {len(missing)} sheets to project '{project_key}'")
    return True


def remove_project() -> bool:
    if not ensure_env_file():
        return False

    config = refresh_secure_config()
    projects = load_current_projects(config)
    if not projects:
        print("❌ No projects configured")
        return False

    print("🏗️  Configured Projects:")
    project_key = select_project(projects)
    if not project_key:
        return False

    confirm = input(
        f"Are you sure you want to remove project '{project_key}' and all its sheet entries? (y/N): "
    ).strip().lower()
    if confirm != "y":
        print("❌ Operation cancelled")
        return False

    env_values = load_env_values()
    slot = determine_project_slot(project_key, env_values)
    name_key, id_key = project_env_keys(slot)
    remove_env_var(name_key)
    remove_env_var(id_key)
    removed = remove_standard_sheets(project_key)

    refresh_secure_config()

    print(f"✅ Removed project '{project_key}' and {removed} associated sheet entries")
    return True


def test_project_config(project_key: Optional[str] = None) -> bool:
    if not ensure_env_file():
        return False

    config = refresh_secure_config()
    projects = load_current_projects(config)
    if not projects:
        print("❌ No projects configured")
        return False

    if project_key and project_key not in projects:
        print(f"❌ Project '{project_key}' not found")
        return False

    if not project_key:
        print("Select project to test:")
        project_key = select_project(projects)
        if not project_key:
            return False

    token_file = config.get("google_token_file", "config/token.pickle")
    if not Path(token_file).exists():
        print("❌ No Google authentication token found!")
        print("   Complete OAuth authentication before testing (see docs/SECURITY_CONFIG_GUIDE.md)")
        return False

    print("✅ Authentication token found")
    print(f"🔧 Testing access to project '{project_key}' using managed environment...")

    try:
        temp_script = Path("/tmp/test_google_access.py")
        temp_script.write_text(
            """
import sys
from src.secure_config import SecureConfig
from src.connectors.google_sheets_connector import GoogleSheetsConnector

config = SecureConfig().build_legacy_config()
connector = GoogleSheetsConnector(config)
print(f"📋 Testing access to project {sys.argv[1]} sheets...")
try:
    sheets = connector.list_available_sheets(f"projects.{sys.argv[1]}")
    if sheets:
        print(f"✅ Successfully accessed {len(sheets)} sheets:")
        for sheet in sheets[:3]:
            print(f"   - {sheet}")
        if len(sheets) > 3:
            print(f"   ... and {len(sheets) - 3} more")
        print("\n🎉 Google Sheets access is working!")
    else:
        print("⚠️  No sheets found or access denied")
except Exception as exc:
    print(f"❌ Test failed: {exc}")
""",
            encoding="utf-8",
        )

        command = (
            "cd "
            + str(SCRIPT_DIR)
            + " && source buildbridge_env/bin/activate && python3 /tmp/test_google_access.py "
            + project_key
        )
        result = subprocess.run(["bash", "-lc", command], capture_output=True, text=True, timeout=45)
        temp_script.unlink(missing_ok=True)

        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Test timed out - check network or authentication status")
        return False
    except Exception as exc:
        print(f"❌ Configuration test failed: {exc}")
        return False


def main() -> None:
    while True:
        print("\n🏗️  BuildBridge-MCP Project Manager")
        print("=" * 40)
        print("1. Add new project")
        print("2. List projects")
        print("3. Complement existing project")
        print("4. Remove project")
        print("5. Test project access")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ").strip()

        if choice == "1":
            add_project()
        elif choice == "2":
            list_projects()
        elif choice == "3":
            complement_project()
        elif choice == "4":
            remove_project()
        elif choice == "5":
            test_project_config()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)
    main()
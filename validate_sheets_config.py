#!/usr/bin/env python3
"""Validate Google Sheets configuration using the secure config manager."""

from pathlib import Path
import sys

from dotenv import load_dotenv

from src.secure_config import SecureConfig


def load_configuration() -> dict:
    root_dir = Path(__file__).resolve().parent
    load_dotenv(root_dir / ".env", override=True)
    return SecureConfig().build_legacy_config()


def validate_sheet_config() -> bool:
    print("🔍 Validating Google Sheets Configuration")
    print("=" * 50)

    config = load_configuration()

    required_google_keys = [
        "google_auth_method",
        "google_credentials_file",
        "google_token_file",
    ]

    missing = [key for key in required_google_keys if key not in config]
    if missing:
        for key in missing:
            print(f"❌ Missing {key} in environment configuration")
        return False

    for key in required_google_keys:
        print(f"✅ {key}: {config[key]}")

    creds_file = Path(config.get("google_credentials_file", "config/client_secret.json"))
    if creds_file.exists():
        print(f"✅ OAuth credentials file exists: {creds_file}")
    else:
        print(f"❌ OAuth credentials file not found: {creds_file}")
        return False

    google_sheets = config.get("google_sheets", {})
    if not google_sheets:
        print("⚠️  No Google Sheets configuration found in environment variables")
        return False

    projects = google_sheets.get("projects", {})
    if not projects:
        print("⚠️  No projects defined. Add GOOGLE_SHEETS_PROJECT_* variables to .env")
        return False

    print(f"\n📊 Found {len(google_sheets)} sheet configurations:")

    valid_sheets = 0
    actual_sheets = 0
    for sheet_name, sheet_config in google_sheets.items():
        if sheet_name == "projects" or sheet_name.startswith("//"):
            continue

        if not isinstance(sheet_config, dict):
            continue

        actual_sheets += 1
        print(f"\n🔍 Checking sheet: {sheet_name}")

        sheet_id = sheet_config.get("sheet_id", "")
        range_val = sheet_config.get("range", "")

        if not sheet_id:
            print("❌ Missing sheet_id configuration")
        elif sheet_id.startswith("projects."):
            _, project_key = sheet_id.split(".", 1)
            if project_key in projects:
                resolved_id = projects[project_key]
                print(f"✅ sheet_id reference resolved: {resolved_id[:20]}...")
            else:
                print(f"❌ Project '{project_key}' not found in configured projects")
        else:
            print(f"✅ sheet_id: {sheet_id[:20]}...")

        if not range_val:
            print("❌ Missing range configuration")
        else:
            print(f"✅ range: {range_val}")

        if sheet_id and range_val:
            if sheet_id.startswith("projects."):
                _, project_key = sheet_id.split(".", 1)
                if project_key in projects:
                    valid_sheets += 1
            else:
                valid_sheets += 1

    print(f"\n📈 Summary: {valid_sheets}/{actual_sheets} sheets properly configured")

    if valid_sheets == actual_sheets and actual_sheets > 0:
        print("✅ All sheet configurations are valid!")
        return True

    print("⚠️  Some sheets need configuration")
    return False


if __name__ == "__main__":
    success = validate_sheet_config()
    if success:
        print("\n🎉 Configuration validation passed!")
        print("You can now test with: python test_google_drive.py")
    else:
        print("\n⚠️  Please fix the configuration issues above")
        sys.exit(1)
#!/usr/bin/env python3
"""
Validate Google Sheets configuration
"""

import json
import sys
import os

def validate_sheet_config():
    """Validate the Google Sheets configuration in credentials.json"""

    print("🔍 Validating Google Sheets Configuration")
    print("=" * 50)

    # Check if credentials.json exists
    if not os.path.exists('config/credentials.json'):
        print("❌ config/credentials.json not found")
        return False

    # Load configuration
    try:
        with open('config/credentials.json', 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config/credentials.json: {e}")
        return False

    # Check Google auth configuration
    google_config = {}
    required_google_keys = ['google_auth_method', 'google_credentials_file', 'google_token_file']

    for key in required_google_keys:
        if key in config:
            google_config[key] = config[key]
            print(f"✅ {key}: {config[key]}")
        else:
            print(f"❌ Missing {key}")
            return False

    # Check OAuth credentials file
    creds_file = config.get('google_credentials_file', 'config/client_secret.json')
    if os.path.exists(creds_file):
        print(f"✅ OAuth credentials file exists: {creds_file}")
    else:
        print(f"❌ OAuth credentials file not found: {creds_file}")
        return False

    # Check Google Sheets configuration
    if 'google_sheets' not in config:
        print("⚠️  No google_sheets configuration found")
        print("   Add google_sheets section to config/credentials.json")
        return False

    google_sheets = config['google_sheets']
    if not google_sheets:
        print("⚠️  google_sheets section is empty")
        return False

    # Check if projects section exists
    projects = google_sheets.get('projects', {})

    print(f"\n📊 Found {len(google_sheets)} sheet configurations:")

    valid_sheets = 0
    actual_sheets = 0
    for sheet_name, sheet_config in google_sheets.items():
        # Skip comment lines and projects section
        if sheet_name.startswith('//') or sheet_name == 'projects':
            continue

        actual_sheets += 1
        print(f"\n🔍 Checking sheet: {sheet_name}")

        if not isinstance(sheet_config, dict):
            print("❌ Sheet configuration must be an object")
            continue

        # Check sheet_id
        sheet_id = sheet_config.get('sheet_id', '')
        if not sheet_id:
            print("❌ Missing sheet_id configuration")
        elif sheet_id.startswith('projects.'):
            # This is a project reference - check if project exists
            _, project_key = sheet_id.split('.', 1)
            if project_key in projects:
                resolved_id = projects[project_key]
                print(f"✅ sheet_id reference resolved: {resolved_id[:20]}...")
            else:
                print(f"❌ Project '{project_key}' not found in projects section")
        elif sheet_id.startswith('YOUR_'):
            print(f"❌ Invalid sheet_id: {sheet_id}")
            print("   Replace with actual Google Sheet ID or project reference")
        else:
            print(f"✅ sheet_id: {sheet_id[:20]}...")

        # Check range
        range_val = sheet_config.get('range', '')
        if not range_val:
            print("❌ Missing range configuration")
        else:
            print(f"✅ range: {range_val}")

        # Validate if sheet is properly configured
        if sheet_id and not sheet_id.startswith('YOUR_') and range_val:
            if sheet_id.startswith('projects.'):
                _, project_key = sheet_id.split('.', 1)
                if project_key in projects:
                    valid_sheets += 1
            else:
                valid_sheets += 1

    print(f"\n📈 Summary: {valid_sheets}/{actual_sheets} sheets properly configured")

    if valid_sheets == actual_sheets:
        print("✅ All sheet configurations are valid!")
        return True
    else:
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
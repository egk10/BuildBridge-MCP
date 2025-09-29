#!/usr/bin/env python3
"""
User-friendly script to add new projects and their Google Sheets to BuildBridge-MCP
"""

import json
import os
import sys
from pathlib import Path

def load_credentials():
    """Load the current credentials configuration"""
    config_path = Path('config/credentials.json')
    if not config_path.exists():
        print("❌ config/credentials.json not found!")
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error reading credentials.json: {e}")
        return None

def save_credentials(config):
    """Save the updated credentials configuration"""
    config_path = Path('config/credentials.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def validate_sheet_access(sheet_id, project_name):
    """Validate that the sheet ID is accessible (basic format check)"""
    if not sheet_id or len(sheet_id.strip()) == 0:
        return False, "Sheet ID cannot be empty"

    # Basic Google Sheets ID validation (should be long alphanumeric string)
    if len(sheet_id) < 20:
        return False, "Sheet ID appears to be too short (should be ~40+ characters)"

    # Check if it contains only valid characters
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', sheet_id):
        return False, "Sheet ID contains invalid characters"

    return True, "Sheet ID format appears valid"

def add_project():
    """Add a new project with its sheets"""
    print("🏗️  BuildBridge-MCP Project Addition Tool")
    print("=" * 50)

    # Load current configuration
    config = load_credentials()
    if not config:
        return False

    # Get project details
    print("\n📝 Enter project details:")
    project_name = input("Project name (e.g., 'downtown_toronto'): ").strip()
    if not project_name:
        print("❌ Project name cannot be empty")
        return False

    # Convert to valid key format
    project_key = project_name.lower().replace(' ', '_').replace('-', '_')

    sheet_id = input("Google Sheet ID: ").strip()
    valid, message = validate_sheet_access(sheet_id, project_name)
    if not valid:
        print(f"❌ {message}")
        return False

    # Check if project already exists
    if 'google_sheets' not in config:
        config['google_sheets'] = {}

    if 'projects' not in config['google_sheets']:
        config['google_sheets']['projects'] = {}

    if project_key in config['google_sheets']['projects']:
        overwrite = input(f"⚠️  Project '{project_key}' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Operation cancelled")
            return False

    # Add project to projects section
    config['google_sheets']['projects'][project_key] = sheet_id

    # Define standard sheet tabs for construction projects
    standard_sheets = [
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
        ("quality_control", "Quality Control")
    ]

    print(f"\n📊 Adding standard sheet configurations for project '{project_name}':")

    # Add sheet configurations
    for sheet_key, sheet_name in standard_sheets:
        config_key = f"{project_key}_{sheet_key}"
        config['google_sheets'][config_key] = {
            "sheet_id": f"projects.{project_key}",
            "range": f"{sheet_name}!A1:Z1000"
        }
        print(f"  ✅ {config_key} -> {sheet_name}")

    # Save configuration
    if save_credentials(config):
        print("\n🎉 Project added successfully!")
        print(f"   Project key: {project_key}")
        print(f"   Sheet ID: {sheet_id}")
        print(f"   Added {len(standard_sheets)} sheet configurations")

        # Offer to test the configuration
        test_now = input("\n🧪 Test the new project configuration? (y/N): ").strip().lower()
        if test_now == 'y':
            print("\n🧪 Testing configuration...")
            test_project_config(project_key)

        return True

    return False

def test_project_config(project_key):
    """Test that the project configuration is valid"""
    print("🔧 Checking project access configuration...")

    # Check if token exists first
    config = load_credentials()
    if not config:
        print("❌ Failed to load credentials")
        return False

    token_file = config.get('google_token_file', 'config/token.pickle')
    if not os.path.exists(token_file):
        print("❌ No Google authentication token found!")
        print("   You need to complete OAuth authentication first.")
        print("   Run: python test_google_drive.py")
        print("   Then visit the URL, sign in, and paste the authorization code.")
        return False

    print("✅ Authentication token found")
    print(f"🔧 Testing access to project '{project_key}' using virtual environment...")

    try:
        import subprocess

        # Create a simple test script
        test_script = f'''
import sys
sys.path.insert(0, "src")

try:
    from connectors.google_sheets_connector import GoogleSheetsConnector
    import json

    # Load config
    with open("config/credentials.json", "r") as f:
        config = json.load(f)

    connector = GoogleSheetsConnector(config)

    # Test listing available sheets
    print(f"📋 Testing access to project {project_key} sheets...")
    sheets = connector.list_available_sheets(f"projects.{project_key}")

    if sheets:
        print(f"✅ Successfully accessed {{len(sheets)}} sheets:")
        for sheet in sheets[:3]:  # Show first 3
            print(f"   - {{sheet}}")
        if len(sheets) > 3:
            print(f"   ... and {{len(sheets) - 3}} more")
        print("\\n🎉 Google Sheets access is working!")
    else:
        print("⚠️  No sheets found or access denied")

except Exception as e:
    print(f"❌ Test failed: {{e}}")
'''

        # Write test script to temp file
        with open('/tmp/test_google_access.py', 'w') as f:
            f.write(test_script)

        # Run in virtual environment with shorter timeout
        result = subprocess.run([
            'bash', '-c',
            'cd /home/egk/buildbridge-MCP/BuildBridge-MCP && '
            'source buildbridge_env/bin/activate && '
            'python3 /tmp/test_google_access.py'
        ], capture_output=True, text=True, timeout=30)

        # Clean up
        os.remove('/tmp/test_google_access.py')

        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Test timed out - this may indicate network or authentication issues")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def list_projects():
    """List all configured projects"""
    print("🔍 Loading project configuration...")

    config = load_credentials()
    if not config:
        print("❌ Failed to load credentials.json")
        return

    if 'google_sheets' not in config:
        print("❌ No google_sheets section found in config")
        return

    if 'projects' not in config['google_sheets']:
        print("❌ No projects section found in google_sheets")
        return

    projects = config['google_sheets']['projects']
    if not projects:
        print("❌ Projects section is empty")
        return

    print(f"✅ Found {len(projects)} projects")
    print("\n🏗️  Configured Projects:")
    print("=" * 50)

    for key, sheet_id in projects.items():
        print(f"📁 {key}")
        print(f"   Sheet ID: {sheet_id}")

        # Count and list associated sheets
        associated_sheets = []
        for config_key, config_value in config['google_sheets'].items():
            if isinstance(config_value, dict) and 'sheet_id' in config_value:
                sheet_id_ref = config_value['sheet_id']
                if f"projects.{key}" in sheet_id_ref:
                    # Extract sheet name from range
                    range_name = config_value.get('range', '')
                    if '!' in range_name:
                        sheet_name = range_name.split('!')[0]
                        associated_sheets.append(sheet_name)

        print(f"   Sheets: {len(associated_sheets)}")
        if associated_sheets:
            # Sort and display in multiple lines of 4 for better readability
            sorted_sheets = sorted(set(associated_sheets))
            print("   Available sheets:")
            for i in range(0, len(sorted_sheets), 4):
                chunk = sorted_sheets[i:i+4]
                print(f"     • {', '.join(chunk)}")
        else:
            print("   Available sheets: None")
        print()

    print("💡 Tip: Use ↑/↓ arrow keys or scroll to see all output")

def complement_project():
    """Add missing standard sheets to an existing project"""
    config = load_credentials()
    if not config or 'google_sheets' not in config or 'projects' not in config['google_sheets']:
        print("❌ No projects configured")
        return False

    projects = config['google_sheets']['projects']
    if not projects:
        print("❌ No projects configured")
        return False

    print("🏗️  Select project to complement:")
    project_list = list(projects.keys())
    for i, key in enumerate(project_list, 1):
        print(f"  {i}. {key}")

    try:
        choice = input("\nEnter project number: ").strip()
        idx = int(choice) - 1
        if idx < 0 or idx >= len(project_list):
            print("❌ Invalid selection")
            return False

        project_key = project_list[idx]

        # Define standard sheet tabs for construction projects
        standard_sheets = [
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
            ("quality_control", "Quality Control")
        ]

        # Find existing sheets for this project
        existing_sheets = set()
        for config_key, config_value in config['google_sheets'].items():
            if isinstance(config_value, dict) and 'sheet_id' in config_value:
                if config_value['sheet_id'] == f"projects.{project_key}":
                    # Extract sheet type from config key
                    if config_key.startswith(f"{project_key.replace('_', '')}_"):
                        sheet_type = config_key[len(f"{project_key.replace('_', '')}_"):]
                        existing_sheets.add(sheet_type)
                    elif config_key.startswith(f"{project_key}_"):
                        sheet_type = config_key[len(f"{project_key}_"):]
                        existing_sheets.add(sheet_type)

        # Find missing sheets
        missing_sheets = []
        for sheet_key, sheet_name in standard_sheets:
            if sheet_key not in existing_sheets:
                missing_sheets.append((sheet_key, sheet_name))

        if not missing_sheets:
            print(f"✅ Project '{project_key}' already has all standard sheets!")
            return True

        print(f"\n📊 Adding {len(missing_sheets)} missing sheets to project '{project_key}':")
        for sheet_key, sheet_name in missing_sheets:
            config_key = f"{project_key.replace('_', '')}_{sheet_key}"
            config['google_sheets'][config_key] = {
                "sheet_id": f"projects.{project_key}",
                "range": f"{sheet_name}!A1:Z1000"
            }
            print(f"  ✅ {config_key} -> {sheet_name}")

        # Save configuration
        if save_credentials(config):
            print(f"\n🎉 Successfully added {len(missing_sheets)} sheets to project '{project_key}'!")
            return True

    except ValueError:
        print("❌ Invalid input")
        return False

    return False

def remove_project():
    config = load_credentials()
    if not config or 'google_sheets' not in config or 'projects' not in config['google_sheets']:
        print("❌ No projects configured")
        return False

    projects = config['google_sheets']['projects']
    if not projects:
        print("❌ No projects configured")
        return False

    print("🏗️  Configured Projects:")
    for i, key in enumerate(projects.keys(), 1):
        print(f"  {i}. {key}")

    try:
        choice = input("\nEnter project number to remove (or 'cancel'): ").strip()
        if choice.lower() == 'cancel':
            return False

        idx = int(choice) - 1
        if idx < 0 or idx >= len(projects):
            print("❌ Invalid selection")
            return False

        project_key = list(projects.keys())[idx]

        confirm = input(f"Are you sure you want to remove project '{project_key}' and all its sheets? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            return False

        # Remove from projects
        del config['google_sheets']['projects'][project_key]

        # Remove associated sheets
        sheets_to_remove = []
        for config_key in config['google_sheets']:
            if config_key.startswith(f"{project_key}_"):
                sheets_to_remove.append(config_key)

        for key in sheets_to_remove:
            del config['google_sheets'][key]

        if save_credentials(config):
            print(f"✅ Removed project '{project_key}' and {len(sheets_to_remove)} associated sheets")
            return True

    except ValueError:
        print("❌ Invalid input")
        return False

    return False

def main():
    """Main menu"""
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

        if choice == '1':
            add_project()
        elif choice == '2':
            list_projects()
        elif choice == '3':
            complement_project()
        elif choice == '4':
            remove_project()
        elif choice == '5':
            # Test specific project
            config = load_credentials()
            if config and 'google_sheets' in config and 'projects' in config['google_sheets']:
                projects = list(config['google_sheets']['projects'].keys())
                if projects:
                    print("Select project to test:")
                    for i, proj in enumerate(projects, 1):
                        print(f"  {i}. {proj}")
                    try:
                        idx = int(input("Project number: ").strip()) - 1
                        if 0 <= idx < len(projects):
                            test_project_config(projects[idx])
                        else:
                            print("❌ Invalid selection")
                    except ValueError:
                        print("❌ Invalid input")
                else:
                    print("❌ No projects configured")
            else:
                print("❌ No projects configured")
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    main()
#!/usr/bin/env python3
"""
Test script for Google Drive authentication and basic functionality
"""

import sys
import os
import json
sys.path.insert(0, 'src')

from connectors.google_sheets_connector import GoogleSheetsConnector

def test_google_drive_auth():
    """Test Google Drive authentication"""
    print("🔐 Testing Google Drive authentication...")

    # Load config
    try:
        with open('config/credentials.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config/credentials.json not found")
        return False

    # Test authentication
    connector = GoogleSheetsConnector(config)
    success = connector.authenticate_google_drive()

    if success:
        print("✅ Google Drive authentication successful!")
        return True
    else:
        print("❌ Google Drive authentication failed")
        return False

def test_sheets_access():
    """Test basic Google Sheets access"""
    print("\n📊 Testing Google Sheets access...")

    try:
        with open('config/credentials.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config/credentials.json not found")
        return False

    connector = GoogleSheetsConnector(config)

    # Test with sample sheet if configured
    if 'google_sheets' in config and config['google_sheets']:
        for sheet_name, sheet_config in config['google_sheets'].items():
            if 'sheet_id' in sheet_config and sheet_config['sheet_id']:
                print(f"Testing access to sheet: {sheet_name}")
                try:
                    data = connector.get_sheet_data(sheet_config['sheet_id'])
                    print(f"✅ Successfully accessed {sheet_name}")
                    print(f"   Rows: {len(data)}")
                except Exception as e:
                    print(f"❌ Failed to access {sheet_name}: {str(e)}")
            else:
                print(f"⚠️  No sheet_id configured for {sheet_name}")
    else:
        print("⚠️  No Google Sheets configured in credentials.json")

    return True

if __name__ == "__main__":
    print("🧪 BuildBridge-MCP Google Drive Test")
    print("====================================")

    # Test authentication
    auth_success = test_google_drive_auth()

    if auth_success:
        # Test sheets access
        test_sheets_access()

    print("\n✅ Test complete!")
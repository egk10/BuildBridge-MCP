#!/bin/bash
"""
Setup script for Google Drive authentication with BuildBridge-MCP

This script helps you set up OAuth2 authentication for personal Google Drive access.
"""

set -e

echo "🔧 BuildBridge-MCP Google Drive Setup"
echo "====================================="
echo ""

# Check if we're in the right directory
if [ ! -f "src/connectors/google_sheets_connector.py" ]; then
    echo "❌ Error: Please run this script from the BuildBridge-MCP root directory"
    exit 1
fi

echo "📋 Prerequisites:"
echo "1. Google Cloud Console account"
echo "2. Google Drive API enabled"
echo "3. OAuth 2.0 credentials created"
echo ""

read -p "Do you have OAuth 2.0 credentials from Google Cloud Console? (y/n): " has_creds

if [ "$has_creds" != "y" ] && [ "$has_creds" != "Y" ]; then
    echo ""
    echo "📖 Follow these steps to create OAuth 2.0 credentials:"
    echo ""
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing one"
    echo "3. Enable the Google Sheets API and Google Drive API"
    echo "4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'"
    echo "5. Choose 'Desktop application' as application type"
    echo "6. Download the JSON file and save it as 'client_secret.json' in config/"
    echo ""
    read -p "Press Enter when you have the credentials file ready..."
fi

# Check if credentials file exists
if [ ! -f "config/client_secret.json" ]; then
    echo ""
    echo "❌ client_secret.json not found in config/ directory"
    echo "Please download your OAuth 2.0 credentials from Google Cloud Console"
    echo "and save them as config/client_secret.json"
    exit 1
fi

echo ""
echo "✅ Found credentials file: config/client_secret.json"

# Update credentials.json with OAuth configuration
echo ""
echo "📝 Updating configuration..."

# Create credentials.json if it doesn't exist
if [ ! -f "config/credentials.json" ]; then
    cp config/credentials.json.template config/credentials.json
    echo "Created config/credentials.json from template"
fi

# Update the Google auth configuration
python3 -c "
import json
import os

# Read current config
with open('config/credentials.json', 'r') as f:
    config = json.load(f)

# Update Google configuration
config['google_auth_method'] = 'oauth'
config['google_credentials_file'] = 'config/client_secret.json'
config['google_token_file'] = 'config/token.pickle'

# Write back
with open('config/credentials.json', 'w') as f:
    json.dump(config, f, indent=2)

print('Updated config/credentials.json with OAuth settings')
"

echo ""
echo "🔐 Starting OAuth authentication..."
echo "A browser window will open for Google authentication."
echo "Please sign in with your Google account and grant permissions."
echo ""

# Run authentication test
python3 -c "
import sys
import os
sys.path.insert(0, 'src')

from connectors.google_sheets_connector import GoogleSheetsConnector
import json

# Load config
with open('config/credentials.json', 'r') as f:
    config = json.load(f)

# Test authentication
connector = GoogleSheetsConnector(config)
success = connector.authenticate_google_drive()

if success:
    print('')
    print('🎉 Google Drive authentication successful!')
    print('You can now use Google Sheets in your BuildBridge-MCP queries.')
    print('')
    print('Next steps:')
    print('1. Create Google Sheets with your construction data')
    print('2. Update config/credentials.json with your sheet IDs')
    print('3. Test with: python src/main.py --test')
else:
    print('')
    print('❌ Authentication failed. Please check your credentials and try again.')
    sys.exit(1)
"

echo ""
echo "📊 To use Google Sheets in your queries:"
echo "1. Create spreadsheets in Google Drive with construction data"
echo "2. Get the spreadsheet ID from the URL (the long string between /d/ and /edit)"
echo "3. Update the sheet_id values in config/credentials.json"
echo "4. Set local_mode to false in your configuration"
echo ""
echo "Example sheet URL: https://docs.google.com/spreadsheets/d/1ABC123.../edit"
echo "Sheet ID: 1ABC123..."
echo ""
echo "✅ Setup complete!"
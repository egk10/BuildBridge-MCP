# Google Drive Integration Setup Guide
## BuildBridge-MCP Personal Google Drive Access

**Date Created:** September 22, 2025
**Last Updated:** September 22, 2025

This guide provides complete instructions for setting up OAuth2 authentication to access Google Sheets from your personal Google Drive account with BuildBridge-MCP.

## 📋 Prerequisites

Before starting, ensure you have:
- Google Cloud Console account
- Google Drive with construction data spreadsheets
- BuildBridge-MCP codebase (week3-grok branch)
- Python 3.12+ environment

## 🔧 Code Changes Made

The following files have been updated to support OAuth2 authentication:

### 1. `src/connectors/google_sheets_connector.py`
- Added `_perform_oauth_flow()` method for OAuth2 authentication
- Added `_determine_auth_type()` method to choose between service account and OAuth2
- Added `authenticate_google_drive()` method for testing Google Drive access
- Enhanced constructor to support both authentication methods

### 2. `config/credentials.json.template`
- Added `google_auth_method` field ("service_account" or "oauth")
- Added `google_credentials_file` field for OAuth client secrets path
- Added `google_token_file` field for OAuth token storage

### 3. `requirements.txt`
- Added `google-auth-oauthlib>=1.2.0`
- Added `google-auth-httplib2>=0.1.0`

## 🚀 Setup Steps

### Step 1: Create Google Cloud Project & Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

### Step 2: Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Download the JSON file (contains client_id, client_secret, etc.)
5. Save the downloaded file as `config/client_secret.json`

### Step 3: Configure BuildBridge-MCP

1. Copy the credentials template:
   ```bash
   cp config/credentials.json.template config/credentials.json
   ```

2. Update `config/credentials.json`:
   ```json
   {
     "google_auth_method": "oauth",
     "google_credentials_file": "config/client_secret.json",
     "google_token_file": "config/token.pickle",
     "google_sheets": {
       "your_sheet_name": {
         "sheet_id": "your_google_sheet_id_here",
         "range": "A1:Z1000"
       }
     }
   }
   ```

### Step 4: Run Authentication Setup

Execute the setup script:
```bash
./setup_google_drive.sh
```

This will:
- Verify credentials file exists
- Update configuration automatically
- Launch OAuth flow in browser
- Save authentication tokens

**⚠️ Important:** If you get a "500 error" during authentication, you need to configure the OAuth consent screen in Google Cloud Console first. It may take 5 minutes to a few hours for the settings to take effect.

### Step 5: Test the Connection

Run the test script:
```bash
python test_google_drive.py
```

## 📊 Using Google Sheets in Queries

### Getting Sheet IDs
1. Open your Google Sheet in a browser
2. Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
   ```
   Example: `1ABC123xyz...`

### Configuration Example
```json
{
  "google_sheets": {
    "construction_projects": {
      "sheet_id": "1ABC123xyz...",
      "range": "A1:Z1000"
    },
    "material_inventory": {
      "sheet_id": "2DEF456uvw...",
      "range": "Sheet1!A1:Z500"
    }
  }
}
```

### MCP Query Examples
```
"Show me all construction projects from Google Sheets"
"Get material inventory data from my Google Drive"
"Analyze project costs from spreadsheet data"
```

## 🔐 Authentication Methods

BuildBridge-MCP supports two authentication methods:

### OAuth2 (Personal Account)
- **Use Case:** Access personal Google Drive files
- **Setup:** Requires OAuth flow and browser authentication
- **Configuration:** `"google_auth_method": "oauth"`

### Service Account (Organizational)
- **Use Case:** Access shared organizational files
- **Setup:** Requires service account key file
- **Configuration:** `"google_auth_method": "service_account"`

## 🛠️ Troubleshooting

### Common Issues

1. **"500. That's an error" during OAuth authentication**
   - **Cause:** OAuth consent screen not configured in Google Cloud Console
   - **Solution:** Set up OAuth consent screen at https://console.cloud.google.com/apis/credentials/consent
   - **Wait time:** May take 5 minutes to a few hours for settings to take effect
   - **Steps:** Choose "External" user type, fill in app info, add your email as test user

2. **"client_secret.json not found"**
   - Ensure you downloaded OAuth credentials from Google Cloud Console
   - Verify file is saved as `config/client_secret.json`

3. **"Authentication failed"**
   - Check that Google Sheets API and Google Drive API are enabled
   - Verify OAuth consent screen is configured
   - Ensure correct scopes are granted

4. **"Access denied to sheet"**
   - Confirm the sheet is in your Google Drive
   - Check that you've shared the sheet with your account (if needed)
   - Verify the sheet_id is correct

5. **"Token expired"**
   - Delete `config/token.pickle` and re-run setup
   - Re-authenticate through the OAuth flow

### Debug Commands
```bash
# Check configuration
cat config/credentials.json

# Test authentication only
python -c "
import sys
sys.path.insert(0, 'src')
from connectors.google_sheets_connector import GoogleSheetsConnector
import json
with open('config/credentials.json') as f:
    config = json.load(f)
connector = GoogleSheetsConnector(config)
print('Auth success:', connector.authenticate_google_drive())
"

# Check token file
ls -la config/token.pickle
```

## 📁 File Structure

After setup, your config directory should contain:
```
config/
├── credentials.json          # Main configuration
├── credentials.json.template # Template file
├── client_secret.json        # OAuth credentials (downloaded)
└── token.pickle             # OAuth tokens (generated)
```

## 🔄 Updating Authentication

To change authentication methods or refresh tokens:

1. Update `config/credentials.json`
2. Delete `config/token.pickle` (if using OAuth)
3. Re-run `./setup_google_drive.sh`

## 📞 Support

If you encounter issues:
1. Check this guide for common solutions
2. Verify all prerequisites are met
3. Test with the provided test script
4. Check Google Cloud Console for API enablement

## 🎯 Next Steps

After successful setup:
1. Create/populate your construction data spreadsheets
2. Configure sheet IDs in `credentials.json`
3. Test MCP queries with Google Sheets data
4. Consider setting up automated data sync

---

**Note:** Keep `client_secret.json` and `token.pickle` secure and never commit them to version control.
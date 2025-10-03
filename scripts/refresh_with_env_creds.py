#!/usr/bin/env python3
"""Refresh from Google Sheets using .env credentials directly."""

from __future__ import annotations

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Load .env file
env_path = PROJECT_ROOT / '.env'
load_dotenv(env_path)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def get_fresh_credentials():
    """Get credentials using client ID/secret from .env."""
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise Exception("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env")
    
    print(f"🔑 Using OAuth credentials from .env")
    print(f"   Client ID: {client_id[:20]}...")
    
    # Create client config from .env values
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    
    # Try to load existing token first
    token_path = PROJECT_ROOT / 'config' / 'token.pickle'
    creds = None
    
    if token_path.exists():
        print(f"📂 Found existing token at {token_path}")
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            print("✅ Loaded existing token")
        except Exception as e:
            print(f"⚠️  Could not load token: {e}")
    
    # Check if credentials are valid
    if creds and creds.valid:
        print("✅ Token is valid")
        return creds
    
    # Try to refresh if expired
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Token expired, attempting to refresh...")
        try:
            creds.refresh(Request())
            print("✅ Token refreshed successfully")
            # Save refreshed token
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            return creds
        except Exception as e:
            print(f"❌ Refresh failed: {e}")
            print("🔄 Will need to re-authenticate...")
    
    # Need to authenticate
    print("🌐 Starting OAuth authentication flow...")
    print("   A browser window will open for you to sign in")
    
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
    print(f"✅ Token saved to {token_path}")
    
    return creds


def read_project_summary(service, spreadsheet_id, project_name):
    """Read Project Summary data from a spreadsheet."""
    
    print(f"\n📊 Reading {project_name} from Google Sheets...")
    
    try:
        # Read Project Summary tab - entire first few rows to find the data
        range_name = 'Project Summary!A1:Z10'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print(f"   ⚠️  No data found in Project Summary tab")
            return None
        
        # Search for PROJECT:, LOCATION:, CLIENT: labels
        project_data = {
            'Project_Name': 'N/A',
            'Location': 'N/A',
            'Client': 'N/A',
        }
        
        for row in values:
            row_text = ' '.join(str(cell) for cell in row).upper()
            
            # Look for "PROJECT:" label
            for i, cell in enumerate(row):
                cell_upper = str(cell).upper().strip()
                
                if 'PROJECT:' in cell_upper:
                    # Extract the value after "PROJECT:"
                    project_val = cell_upper.replace('PROJECT:', '').strip()
                    if project_val:
                        project_data['Project_Name'] = project_val
                    elif i + 1 < len(row):  # Check next cell
                        project_data['Project_Name'] = str(row[i + 1]).strip()
                
                elif 'LOCATION:' in cell_upper:
                    location_val = cell_upper.replace('LOCATION:', '').strip()
                    if location_val:
                        project_data['Location'] = location_val
                    elif i + 1 < len(row):
                        project_data['Location'] = str(row[i + 1]).strip()
                
                elif 'CLIENT:' in cell_upper:
                    client_val = cell_upper.replace('CLIENT:', '').strip()
                    if client_val:
                        project_data['Client'] = client_val
                    elif i + 1 < len(row):
                        project_data['Client'] = str(row[i + 1]).strip()
        
        print(f"   ✅ {project_name}:")
        print(f"      Project Name: {project_data['Project_Name']}")
        print(f"      Location: {project_data['Location']}")
        print(f"      Client: {project_data['Client']}")
        
        return project_data
            
    except Exception as e:
        print(f"   ❌ Error reading {project_name}: {e}")
        return None


def main():
    """Read all 3 projects from Google Sheets."""
    
    print("=" * 70)
    print("🔄 Refreshing from Google Sheets using .env credentials")
    print("=" * 70)
    
    # Get credentials
    try:
        creds = get_fresh_credentials()
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return 1
    
    # Build service
    service = build('sheets', 'v4', credentials=creds)
    
    # Get project configurations from .env
    projects = {
        'P': os.getenv('GOOGLE_SHEETS_PROJECT_1_ID'),
        'Y': os.getenv('GOOGLE_SHEETS_PROJECT_2_ID'),
        'A': os.getenv('GOOGLE_SHEETS_PROJECT_3_ID'),
    }
    
    print(f"\n📋 Found {len(projects)} projects in .env")
    
    # Read each project
    results = {}
    for project_name, spreadsheet_id in projects.items():
        if spreadsheet_id:
            data = read_project_summary(service, spreadsheet_id, project_name)
            if data:
                results[project_name] = data
    
    print("\n" + "=" * 70)
    print("✅ Summary of what's in Google Sheets RIGHT NOW:")
    print("=" * 70)
    
    for project_name, data in results.items():
        print(f"\n{project_name}:")
        print(f"  Project Name: {data['Project_Name']}")
        print(f"  Client: {data['Client']}")
        print(f"  Location: {data['Location']}")
    
    # Check if anonymized
    print("\n" + "=" * 70)
    print("🔍 Anonymization Status:")
    print("=" * 70)
    
    old_names = ['72 Perth', 'Perth Avenue', 'Yonge St', '17175 Yonge', 'Azure Road', '6071 Azure']
    old_clients = ['Castlepoint', 'Numa', 'Trinity', 'Coptic', 'LDHT']
    
    all_anonymized = True
    for project_name, data in results.items():
        has_old_name = any(old in data['Project_Name'] for old in old_names)
        has_old_client = any(old in data['Client'] for old in old_clients)
        
        if has_old_name or has_old_client:
            print(f"❌ {project_name}: STILL HAS OLD DATA")
            all_anonymized = False
        else:
            print(f"✅ {project_name}: Looks anonymized!")
    
    if all_anonymized:
        print("\n🎉 All projects appear to be anonymized in Google Sheets!")
        print("   Ready to refresh cache and restart server.")
    else:
        print("\n⚠️  Some projects still have old data in Google Sheets")
        print("   You may need to check if edits were saved properly.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

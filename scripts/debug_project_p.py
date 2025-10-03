#!/usr/bin/env python3
"""Debug script to see raw data from Project P's sheet."""

from __future__ import annotations

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / '.env')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle

def main():
    """Read raw data from Project P."""
    
    # Load token
    token_path = PROJECT_ROOT / 'config' / 'token.pickle'
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
    
    service = build('sheets', 'v4', credentials=creds)
    
    # Project P ID
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_PROJECT_1_ID')
    
    print("=" * 70)
    print("🔍 Raw data from Project P - Project Summary tab, rows 1-5")
    print("=" * 70)
    
    # Read first 5 rows, all columns
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Project Summary!A1:Z5'
    ).execute()
    
    values = result.get('values', [])
    
    for i, row in enumerate(values, start=1):
        print(f"\nRow {i}:")
        for j, cell in enumerate(row):
            col = chr(65 + j)  # A, B, C, ...
            print(f"  {col}{i}: {repr(cell)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

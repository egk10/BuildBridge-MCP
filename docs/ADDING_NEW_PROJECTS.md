# How to Add New Projects to BuildBridge-MCP

This guide explains how to add new construction projects to the system. Thanks to the **dynamic data-driven architecture**, adding projects requires **NO CODE CHANGES** - just configuration and data!

## Quick Start (3 Steps)

1. **Add Google Spreadsheet** to `.env` file
2. **Add project configuration** to `config/project_manifest.json`
3. **Refresh cache** from Google Sheets

That's it! The system automatically detects and displays the new project.

---

## Detailed Step-by-Step Guide

### Step 1: Prepare Your Google Spreadsheet

Your project spreadsheet should follow the standard format with these tabs:
- **Project Summary** (required): Contains project name, client, location, budget
- **GCA Stats** (optional): Building area, units, parking data
- **Cost Breakdown Tabs** (optional): Below Grade, Above Grade, Siteworks, etc.

**Key fields in Project Summary tab** (rows 2-5, column headers in column F, values in column K):
```
PROJECT:  Your Project Name
LOCATION: City, Province/State
CLIENT:   Client Name
DATE:     Budget Date
```

### Step 2: Get Google Sheets ID

1. Open your spreadsheet in Google Sheets
2. Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
   ```
3. Save this ID - you'll need it for the next step

### Step 3: Update `.env` Configuration

Add your new project to the `.env` file:

```bash
# Existing projects
GOOGLE_SHEETS_PROJECT_1_NAME=P
GOOGLE_SHEETS_PROJECT_1_ID=1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k

GOOGLE_SHEETS_PROJECT_2_NAME=Y
GOOGLE_SHEETS_PROJECT_2_ID=1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU

GOOGLE_SHEETS_PROJECT_3_NAME=A
GOOGLE_SHEETS_PROJECT_3_ID=1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg

# NEW PROJECT - Add here:
GOOGLE_SHEETS_PROJECT_4_NAME=D
GOOGLE_SHEETS_PROJECT_4_ID=YOUR_SPREADSHEET_ID_HERE
```

**Naming Convention:**
- Single letter (P, Y, A, D) for anonymized projects
- Or descriptive name (Marina_Tower, Downtown_Plaza) for named projects

### Step 4: Update `config/project_manifest.json`

Add your project's tab configuration:

```json
{
  "P": {
    "project_summary": { ... }
  },
  "Y": {
    "project_summary": { ... }
  },
  "A": {
    "project_summary": { ... }
  },
  "D": {
    "project_summary": {
      "sheet_name": "Project Summary",
      "range": "A1:AZ200",
      "parsers": ["extract_summary_metrics"],
      "local_csv": "data/Project_D_Summary.csv"
    },
    "gca_stats": {
      "sheet_name": "GCA Stats",
      "range": "A1:BI200",
      "parsers": ["extract_gca_metrics"],
      "local_csv": "data/Project_D_GCA_Stats.csv"
    }
  }
}
```

**Key Configuration Fields:**
- `sheet_name`: Exact name of the tab in your spreadsheet
- `range`: Cell range to read (A1:AZ200 covers most layouts)
- `parsers`: Which parser function to use (usually `extract_summary_metrics`)
- `local_csv`: CSV backup file path (optional, for offline mode)

### Step 5: Refresh Cache from Google Sheets

Run the refresh script to pull data from your new spreadsheet:

```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/refresh_from_live_sheets.py
```

**What this does:**
- Connects to Google Sheets API using OAuth credentials
- Reads all tabs configured in `project_manifest.json`
- Parses data using specified parsers
- Saves to `cache/normalized/{PROJECT_ID}.json`

**Expected output:**
```
🔄 Refreshing cache from LIVE Google Sheets (not CSV files)...
============================================================
📊 Found 4 projects: ['P', 'Y', 'A', 'D']

🔄 Refreshing from Google Sheets API...

📊 Rebuilding metrics summary...

============================================================
✅ Successfully refreshed 4 projects from live Google Sheets
📄 Metrics summary now includes 4 project entries

  P:
    Name: p
    Client: ABC Development Corp
    Location: Springfield, Ontario
  Y:
    Name: Y
    Client: Summit Investment Group
    Location: 123 Main Street, Lakeside, Ontario
  A:
    Name: A
    Client: XYZ Properties Ltd
    Location: Riverdale, British Columbia
  D:
    Name: Marina Tower
    Client: Coastal Properties Inc
    Location: Vancouver, BC

🎉 Done! Cache refreshed from live Google Sheets.
```

### Step 6: Restart the Server

Restart the production server to load the new project:

```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP

# Stop old server
pkill -f production_mcp_integration

# Start new server
source buildbridge_venv/bin/activate
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"
python src/production_mcp_integration.py --mode server --host localhost --port 8000 > server_runtime.log 2>&1 &
```

### Step 7: Verify the New Project

Open your browser and check:

1. **Web Interface**: http://localhost:8000
   - Should see "Project D" (or your project name) in the dropdown
   
2. **API Endpoint**: 
   ```bash
   curl http://localhost:8000/api/projects | jq '.projects[] | {id, display}'
   ```
   
   Expected output:
   ```json
   {
     "id": "D",
     "display": "Project D"
   }
   ```

3. **Test Query**:
   Open Web Chat V2 and ask: "Show me details for Project D"

---

## How the Dynamic System Works

### Architecture Overview

```
┌─────────────────┐
│   .env file     │  ← Project IDs and Spreadsheet IDs
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ project_manifest.json   │  ← Tab names and ranges
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ refresh_from_live_sheets│  ← Reads from Google Sheets API
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ cache/normalized/*.json │  ← Cached project data
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ production_mcp_integration│  ← Reads cache dynamically
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Web Interface         │  ← Automatically shows all projects
└─────────────────────────┘
```

### Dynamic Display Name Logic

The system automatically determines how to display each project:

```python
# From production_mcp_integration.py, lines ~1640

for project_id in project_manifest.keys():
    # Read from cache file
    cache_file = cache_dir / f"{project_id}.json"
    
    if cache_file.exists():
        cache_data = json.load(cache_file)
        project_name = cache_data['project']['Project_Name']
        
        # Smart formatting:
        if len(project_id) == 1:
            # Single-letter IDs: "Project P", "Project Y"
            display_name = f"Project {project_id.upper()}"
        else:
            # Multi-character IDs: use actual name
            display_name = project_name
    else:
        # Fallback if no cache
        display_name = f"Project {project_id.upper()}"
```

**Display Name Rules:**
- **Single-letter ID** (P, Y, A, D) → "Project P", "Project Y", etc.
- **Multi-character ID** (Marina_Tower) → Uses actual project name from cache
- **No cache available** → Formats the project_id ("Marina Tower")

### Why This is Better Than Hardcoding

**Before (Hardcoded):**
```python
# ❌ BAD: Required code changes for every new project
project_display_names = {
    'Y': '17175 Yonge St',
    'A': 'Azure Road',
    'P': '72 Perth Avenue',
    'D': 'Marina Tower',  # ← Manual update needed
    'E': 'Downtown Plaza',  # ← Manual update needed
}
```

**After (Dynamic):**
```python
# ✅ GOOD: Scales automatically with configuration
for project_id in project_manifest.keys():
    cache_file = cache_dir / f"{project_id}.json"
    if cache_file.exists():
        cache_data = json.load(cache_file)
        display_name = get_smart_display_name(cache_data, project_id)
```

**Benefits:**
1. **No Code Changes**: Add projects in config only
2. **Automatic Discovery**: Server finds all projects from manifest
3. **Data-Driven**: Display names come from actual Google Sheets data
4. **Consistent**: Same data source for cache and display
5. **Maintainable**: No hardcoded lists to keep in sync

---

## Removing Projects

To remove a project:

1. **Remove from `.env`**: Delete the `GOOGLE_SHEETS_PROJECT_X_NAME` and `_ID` lines
2. **Remove from `project_manifest.json`**: Delete the project's configuration block
3. **Delete cache** (optional): `rm cache/normalized/{PROJECT_ID}.json`
4. **Restart server**

The project will no longer appear in the Web interface or API responses.

---

## Troubleshooting

### Problem: New project doesn't appear

**Solution:**
1. Check `.env` file has correct project number sequence (1, 2, 3, 4, not 1, 2, 3, 5)
2. Verify `project_manifest.json` has correct project_id as key
3. Run refresh script and check for errors
4. Verify cache file exists: `ls cache/normalized/{PROJECT_ID}.json`
5. Restart server

### Problem: "Unable to parse range" error

**Solution:**
- Check `sheet_name` in `project_manifest.json` matches exact tab name in Google Sheets
- Tab names are case-sensitive: "BG1" ≠ "bg1" ≠ "Below Grade 1"

### Problem: Project shows "N/A" or empty data

**Solution:**
- Verify spreadsheet has data in "Project Summary" tab
- Check data is in correct format (labels in column F, values in column K)
- Run refresh script with debug output:
  ```bash
  python scripts/debug_project_{ID}.py
  ```

### Problem: OAuth authentication fails

**Solution:**
- Delete expired token: `rm config/token.pickle`
- Run refresh script again - it will prompt for re-authentication
- Browser will open for you to authorize the app

---

## Example: Adding a Multi-Project Scenario

Let's add 3 new projects at once:

### 1. Update `.env`
```bash
GOOGLE_SHEETS_PROJECT_4_NAME=Marina_Tower
GOOGLE_SHEETS_PROJECT_4_ID=1ABC...xyz

GOOGLE_SHEETS_PROJECT_5_NAME=Downtown_Plaza
GOOGLE_SHEETS_PROJECT_5_ID=1DEF...uvw

GOOGLE_SHEETS_PROJECT_6_NAME=Riverside_Condos
GOOGLE_SHEETS_PROJECT_6_ID=1GHI...rst
```

### 2. Update `project_manifest.json`
```json
{
  "P": { ... },
  "Y": { ... },
  "A": { ... },
  "Marina_Tower": {
    "project_summary": {
      "sheet_name": "Project Summary",
      "range": "A1:AZ200",
      "parsers": ["extract_summary_metrics"]
    }
  },
  "Downtown_Plaza": {
    "project_summary": {
      "sheet_name": "Project Summary",
      "range": "A1:AZ200",
      "parsers": ["extract_summary_metrics"]
    }
  },
  "Riverside_Condos": {
    "project_summary": {
      "sheet_name": "Executive Summary",
      "range": "A1:AZ200",
      "parsers": ["extract_summary_metrics"]
    }
  }
}
```

### 3. Refresh and Restart
```bash
python scripts/refresh_from_live_sheets.py
pkill -f production_mcp_integration
# ... start server commands ...
```

### 4. Result
The Web interface now shows **6 projects** automatically:
- Project P
- Project Y
- Project A
- Marina Tower
- Downtown Plaza
- Riverside Condos

**No code changes required!** 🎉

---

## Best Practices

### Project Naming
- **Single-letter IDs**: Use for anonymized/confidential projects (P, Y, A, D)
- **Descriptive IDs**: Use for public/internal projects (Marina_Tower, Phase_2_East)
- **Avoid spaces**: Use underscores instead (`Downtown_Plaza` not `Downtown Plaza`)

### Spreadsheet Organization
- Keep consistent tab names across all projects
- Use standard layouts (labels in column F, values in column K)
- Include all required fields: PROJECT, LOCATION, CLIENT, DATE

### Cache Management
- Refresh cache after spreadsheet updates: `python scripts/refresh_from_live_sheets.py`
- Cache files are gitignored (not committed to repo)
- Schedule automatic refreshes for production (Week 4+ feature)

### Security
- Never commit `.env` file with real spreadsheet IDs
- Use anonymized names for confidential projects
- Keep OAuth tokens secure (`config/token.pickle` is gitignored)

---

## Summary

Adding projects to BuildBridge-MCP is now:
- ✅ **Configuration-based**: No code changes required
- ✅ **Data-driven**: Display names from actual Google Sheets
- ✅ **Automatic**: Server discovers projects dynamically
- ✅ **Scalable**: Works with 3 projects or 300 projects
- ✅ **Maintainable**: Single source of truth (project_manifest.json)

**Time to add a new project: ~5 minutes**
- 2 min: Update config files
- 2 min: Refresh cache
- 1 min: Restart server and verify

Compare to the old hardcoded approach: ~30 minutes of code changes, testing, and debugging! 🚀

---

**Last Updated**: October 3, 2025  
**Version**: 2.0 (Dynamic Architecture)

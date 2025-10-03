# Web Chat V2 Showing Old Names - Root Cause Analysis
**Date:** October 3, 2025 - 11:24 AM  
**Status:** 🔴 **ISSUE IDENTIFIED - ACTION REQUIRED**

---

## 🎯 The Problem

After editing your 3 Google Spreadsheets to anonymize them, the **Web Chat V2 interface still shows the OLD project names** (72 Perth, 17175 Yonge St, Azure Road).

---

## 🔍 Root Cause Analysis

### The Data Flow (How It SHOULD Work):
```
Google Spreadsheets (✅ Anonymized by you)
          ↓
    Refresh Script
          ↓
Cache Files (cache/normalized/*.json)
          ↓
Production Server (reads from cache)
          ↓
Web Chat V2 Interface
```

### What's Actually Happening:
```
Google Spreadsheets (✅ Anonymized by you)
          ❌ CAN'T READ - TAB NAME ERROR
    
CSV Backup Files (❌ Still have old names)
          ↓
refresh_manifest_LOCAL.py (reads CSV files)
          ↓
Cache Files (❌ Generated with old names from CSV)
          ↓
Production Server (✅ reads from cache correctly)
          ↓
Web Chat V2 (❌ Shows old names from cache)
```

---

## 🐛 The Specific Error

When trying to refresh from **live Google Sheets**, we get:

```
HttpError 400: Unable to parse range: Below Grade 1 Detail!A1:R200
```

This error means:
- The Google Sheets API cannot find a tab named "Below Grade 1 Detail"
- This tab was configured in `config/project_manifest.json`
- **Either the tab was renamed OR deleted when you edited the spreadsheet**

---

##  What Likely Happened

When you edited the spreadsheets to anonymize them, you might have:

1. **Renamed sheet tabs** (e.g., "Below Grade 1 Detail" → something else)
2. **Deleted sheet tabs** that weren't needed
3. **Changed tab order** or structure

The system's configuration in `config/project_manifest.json` still references the **old tab names**.

---

## ✅ Solutions - Pick ONE

### **Option 1: Check & Fix Tab Names in Google Sheets** (Recommended)

**Step 1:** Open Project Y spreadsheet:
https://docs.google.com/spreadsheets/d/1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU/edit

**Step 2:** Check if these tabs exist:
- "Project Summary" (✅ should exist)
- "GCA Stats" (✅ should exist)
- **"Below Grade 1 Detail"** (❌ This is the problem - does it exist?)

**Step 3a:** If "Below Grade 1 Detail" was renamed:
- Rename it back to "Below Grade 1 Detail" (exact name, with spaces)

**Step 3b:** If "Below Grade 1 Detail" doesn't exist:
- Remove it from `config/project_manifest.json` for Project Y
- We only need "Project Summary" and "GCA Stats" tabs anyway

**Step 4:** Run refresh script again:
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/refresh_from_live_sheets.py
```

---

### **Option 2: Update CSV Files** (Quick but less ideal)

Since the system currently reads from CSV files (local mode), just update those:

```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP/data

# Update CSV files with anonymized names
find . -name "*.csv" -type f -exec sed -i \
  's/72 Perth Avenue/Northside Residential Complex/g; \
   s/72 Perth/Northside/g; \
   s/17175 Yonge St/Central Plaza Development/g; \
   s/24021 - 17175 Yonge St/Central Plaza Development/g; \
   s/6071 Azure Road/Westgate Towers/g; \
   s/24019 - Azure Road/Westgate Towers/g; \
   s/Castlepoint Numa/ABC Development Corp/g; \
   s/Trinity Coptic Foundation/Summit Investment Group/g; \
   s/LDHT Holdings/XYZ Properties Ltd/g; \
   s/Toronto, ON/Springfield, Ontario/g; \
   s/Newmarket, Ontario/Lakeside, Ontario/g; \
   s/Richmond, British Columbia/Riverdale, British Columbia/g' {} \;

# Regenerate cache from updated CSV files
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/refresh_manifest_local.py --force

# Rename cache files to uppercase
cd cache/normalized
mv a.json A.json 2>/dev/null || true
mv p.json P.json 2>/dev/null || true
mv y.json Y.json 2>/dev/null || true

# Restart server
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
pkill -f production_mcp_integration
nohup bash start_web_server.sh > server_runtime.log 2>&1 &
```

**Pros:**
- Quick fix (5 minutes)
- Uses existing working infrastructure

**Cons:**
- CSV files become your "source of truth" instead of Google Sheets
- Won't reflect future changes you make in Google Sheets
- Not ideal long-term

---

### **Option 3: Simplify Tab Configuration** (Best long-term)

Only use the essential tabs that we know exist:

**Edit** `config/project_manifest.json`:

```json
"Y": {
  "project_summary": {
    "sheet_name": "Project Summary",
    "range": "A1:AZ200",
    "parsers": ["extract_summary_metrics"],
    "local_csv": "data/Copy of 24021 - 17175 Yonge St. - SKYGRiD Master Estimate - Project Summary.csv"
  },
  "gca_stats": {
    "sheet_name": "GCA Stats",
    "range": "A1:BI200",
    "parsers": ["extract_gca_metrics"],
    "local_csv": "data/Copy of 24021 - 17175 Yonge St. - SKYGRiD Master Estimate - GCA Stats.csv"
  }
  // REMOVED: "below_grade" section - not essential for current functionality
}
```

Then retry refresh from live sheets.

---

## 🎯 My Recommendation

**Go with Option 3 + Option 1 combined:**

1. **First:** Open the Google Spreadsheet and check what tabs actually exist
2. **Then:** Update `config/project_manifest.json` to only reference tabs that exist
3. **Finally:** Run `refresh_from_live_sheets.py` to pull from your anonymized sheets

This way you'll have a clean, working system that uses your anonymized Google Sheets as the source of truth.

---

## 📝 Immediate Action Items

**Tell me:**
1. Did you rename or delete the "Below Grade 1 Detail" tab in the Project Y spreadsheet?
2. What tabs DO exist in each of the 3 spreadsheets now?
3. Do you want me to:
   - Help you fix the tab names in Google Sheets? (Option 1)
   - Just update the CSV files quickly? (Option 2)
   - Simplify the configuration? (Option 3)

---

## 🔄 About the "Going Back and Forth" Issue

You're right - we DID set this up before! Here's what happened:

**Oct 1 (Commit b070ba7):** System was changed to read from **cache files** instead of live Google Sheets. This was intentional for performance.

**The cache refresh scripts:**
- `refresh_manifest_LOCAL.py` - Reads from CSV files (for offline dev)
- `refresh_from_live_sheets.py` - Reads from Google Sheets (what we just tried)

The confusion happened because:
1. You edited Google Sheets (✅ correct)
2. The cache needs to be regenerated to pick up changes
3. The LOCAL refresh script was using CSV files (old data)
4. Trying to read from live sheets hit the tab name issue

**We're not going backwards** - we're just hitting a configuration mismatch between what the code expects ("Below Grade 1 Detail" tab) and what exists in your edited spreadsheet.

---

**Last Updated:** October 3, 2025 - 11:25 AM  
**Status:** Waiting for your input on tab names and preferred solution

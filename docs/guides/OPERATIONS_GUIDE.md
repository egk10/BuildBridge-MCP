# BuildBridge-MCP Operations Guide
**Version**: 2.0.0  
**Last Updated**: October 2, 2025

## Table of Contents
1. [Changing Project Names](#changing-project-names)
2. [Replacing Spreadsheets](#replacing-spreadsheets)
3. [Adding New Projects](#adding-new-projects)
4. [Removing Projects](#removing-projects)
5. [Updating Ground Truth Data](#updating-ground-truth-data)
6. [Cache Management](#cache-management)

---

## Changing Project Names

### Scenario
You need to rename a project (e.g., "Project P (Northside Residential)" → "Project P (Northside Residential) - Phase 2")

### Impact Assessment
**Affected Components**:
- ✅ Configuration file (`config/project_manifest.json`)
- ✅ Cache files (`cache/*.json`)
- ✅ Ground truth test data (`tests/ground_truth.json`)
- ⚠️ **Existing queries/data preserved** (data keyed by Project_ID, not name)

### Step-by-Step Procedure

#### 1. Update Project Manifest
**File**: `config/project_manifest.json`

```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
nano config/project_manifest.json
```

**Find the project entry** (search for the Project_ID):
```json
{
  "project_id": "72_perth",
  "project_name": "Project P (Northside Residential)",  // ← Change this
  "spreadsheet_id": "1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg",
  ...
}
```

**Update to**:
```json
{
  "project_id": "72_perth",
  "project_name": "Project P (Northside Residential) - Phase 2",  // ← New name
  "spreadsheet_id": "1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg",
  ...
}
```

**💡 Note**: Keep `project_id` the same! This is the primary key.

#### 2. Clear Project Cache
**Purpose**: Force re-fetch of data with new project name

```bash
# Option A: Clear specific project cache
rm cache/normalized/graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json

# Option B: Clear all caches (safe, will regenerate)
rm cache/normalized/*.json
rm cache/schemas/*.json
rm cache/test_graph_*.json
```

#### 3. Update Ground Truth (If Needed)
**File**: `tests/ground_truth.json`

**Only update if test queries reference the project name specifically**:
```json
{
  "projects": {
    "72_perth": {
      "name": "Project P (Northside Residential) - Phase 2",  // ← Update here
      "total_gca_sf": 214384,
      ...
    }
  }
}
```

**💡 Tip**: Most tests use `project_id` not `name`, so this step is often optional.

#### 4. Restart Server
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
# Kill existing server
pkill -f production_mcp_integration.py

# Start fresh
bash ./start_web_server.sh
```

#### 5. Validate Changes
```bash
# Test that new name appears in queries
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all projects", "query_type": "ai_query", "include_data_context": true}'

# Should show: "Project P (Northside Residential) - Phase 2"
```

#### 6. Run Proof Tests
```bash
python tests/proof_tester.py
# Verify all tests still pass
```

### Expected Outcome
- ✅ New project name visible in AI responses
- ✅ All existing data preserved
- ✅ All tests continue passing
- ✅ Cache regenerated with new metadata

---

## Replacing Spreadsheets

### Scenario
You need to replace a project's Google Spreadsheet with a new one (e.g., updated estimate)

### Important Considerations
⚠️ **CRITICAL**: Replacing a spreadsheet will:
- **Reset all cached data** for that project
- **Require tab name verification** (tabs must match expected structure)
- **Potentially break ground truth** if values changed

### Step-by-Step Procedure

#### 1. Prepare New Spreadsheet
**Requirements**:
- [ ] Spreadsheet shared with BuildBridge service account
- [ ] Tab names match original (e.g., "Project Summary", "GCA Stats", "Exec Summary")
- [ ] Column headers match expected format
- [ ] Data types consistent (numbers as numbers, not text)

**Get the new Spreadsheet ID**:
```
URL: https://docs.google.com/spreadsheets/d/[THIS_IS_THE_SPREADSHEET_ID]/edit
Example: 1ABCDEF-ghijk123456789-lmnopqrstuv
```

#### 2. Update Project Manifest
**File**: `config/project_manifest.json`

```json
{
  "project_id": "72_perth",
  "project_name": "Project P (Northside Residential)",
  "spreadsheet_id": "1ABCDEF-ghijk123456789-lmnopqrstuv",  // ← NEW ID
  "tabs": {
    "project_summary": "Project Summary",     // ← Verify these match new spreadsheet
    "gca_stats": "GCA Stats",
    "exec_summary": "Exec Summary"
  }
}
```

#### 3. Clear ALL Caches for Safety
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP

# Remove old spreadsheet caches (use old ID)
rm cache/test_graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json
rm cache/normalized/graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json
rm cache/schemas/graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json

# Or clear everything to be safe
rm -rf cache/normalized/* cache/schemas/* cache/test_graph_*.json
```

#### 4. Validate Spreadsheet Structure
**Run validation script**:
```bash
python validate_sheets_config.py --project-id 72_perth
```

**Expected output**:
```
✅ Spreadsheet accessible
✅ Tab 'Project Summary' found
✅ Tab 'GCA Stats' found  
✅ Tab 'Exec Summary' found
✅ Required columns present
```

**If validation fails**:
- Check tab names match exactly (case-sensitive!)
- Verify service account has access
- Check column headers match expected format

#### 5. Test Data Fetch
```bash
# Start Python interpreter
python3

# Test loading the new spreadsheet
from src.google_sheets_connector import GoogleSheetsConnector
connector = GoogleSheetsConnector()
data = connector.fetch_project_data("72_perth")
print(f"Loaded {len(data)} rows")
exit()
```

**Expected**: Should print number of rows without errors

#### 6. Update Ground Truth
**File**: `tests/ground_truth.json`

**⚠️ CRITICAL**: Values WILL change with new spreadsheet!

```bash
# Extract new values from spreadsheet
python3 << 'EOF'
from src.google_sheets_connector import GoogleSheetsConnector
import json

connector = GoogleSheetsConnector()
data = connector.fetch_project_data("72_perth")

# Print key metrics for updating ground truth
project = data[0] if data else {}
print(f"Total Budget: {project.get('Total_Budget', 0)}")
print(f"Total Direct Cost: {project.get('Total_Direct_Cost', 0)}")
print(f"Total GCA (SF): {project.get('Total_GCA_SF', 0)}")
print(f"Parking Stalls: {project.get('Parking_Stalls', 0)}")
print(f"Location: {project.get('Location', 'N/A')}")
EOF
```

**Update `tests/ground_truth.json` with new values**:
```json
{
  "projects": {
    "72_perth": {
      "name": "Project P (Northside Residential)",
      "total_gca_sf": 214384,           // ← Update if changed
      "parking_stalls": 31,              // ← Update if changed
      "total_direct_cost": 897836.0,    // ← Update if changed
      "location": "Toronto, ON"          // ← Update if changed
    }
  },
  "portfolio_totals": {
    "total_budget": 70780179.0,         // ← Recalculate portfolio totals!
    "total_direct_cost": 8644684.0      // ← Recalculate portfolio totals!
  }
}
```

**💡 Formula for Portfolio Totals**:
```python
# Total Budget = Sum of all project budgets
# Total Direct Cost = Sum of all project direct costs

# Example:
72_perth_budget + 17175_yonge_budget + azure_road_budget = total_budget
897836 + 7746848 + 0 = 8644684  # Direct cost example
```

#### 7. Restart Server
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
pkill -f production_mcp_integration.py
bash ./start_web_server.sh
```

#### 8. Run Full Test Suite
```bash
python tests/proof_tester.py
```

**Expected Results**:
- ✅ All tests should pass with updated ground truth
- ❌ Tests will FAIL if ground truth not updated correctly

**If tests fail**:
1. Check `tests/proof_test_results.json` for actual vs. expected values
2. Update ground truth with actual values
3. Rerun tests until all pass

#### 9. Document Changes
**Create changelog entry**:
```bash
echo "$(date '+%Y-%m-%d'): Replaced spreadsheet for 72_perth" >> CHANGELOG.md
echo "  - Old ID: 1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg" >> CHANGELOG.md
echo "  - New ID: 1ABCDEF-ghijk123456789-lmnopqrstuv" >> CHANGELOG.md
echo "  - Reason: [Your reason here]" >> CHANGELOG.md
```

### Expected Outcome
- ✅ New spreadsheet data loaded
- ✅ Ground truth updated and verified
- ✅ All tests passing
- ✅ Old cache cleared
- ✅ Changes documented

---

## Adding New Projects

### Scenario
You want to add a 4th project to BuildBridge-MCP

### Step-by-Step Procedure

#### 1. Prepare Spreadsheet
- [ ] Create Google Spreadsheet with required tabs
- [ ] Share with BuildBridge service account: `buildbridge@...iam.gserviceaccount.com`
- [ ] Verify data format matches existing projects
- [ ] Get Spreadsheet ID from URL

#### 2. Add to Project Manifest
**File**: `config/project_manifest.json`

```json
{
  "projects": [
    // ... existing projects ...
    {
      "project_id": "new_project",           // ← Unique ID (lowercase, underscores)
      "project_name": "New Project Name",    // ← Display name
      "spreadsheet_id": "YOUR_SPREADSHEET_ID",
      "tabs": {
        "project_summary": "Project Summary",
        "gca_stats": "GCA Stats",
        "exec_summary": "Exec Summary"
      },
      "data_mappings": {
        "project_name": {
          "tab": "project_summary",
          "cell": "B2"
        },
        "total_budget": {
          "tab": "exec_summary",
          "cell": "C5"
        }
        // ... add all required mappings ...
      }
    }
  ]
}
```

**💡 Tip**: Copy an existing project's mappings and adjust as needed

#### 3. Add to Ground Truth
**File**: `tests/ground_truth.json`

```json
{
  "projects": {
    "new_project": {
      "name": "New Project Name",
      "total_gca_sf": 0,              // ← Extract from spreadsheet
      "parking_stalls": 0,
      "total_direct_cost": 0,
      "location": "City, Province"
    }
  },
  "portfolio_totals": {
    "total_projects": 4,              // ← Increment!
    "total_budget": 0,                // ← Recalculate!
    "total_direct_cost": 0,           // ← Recalculate!
    "total_gca_sf": 0,                // ← Recalculate!
    "total_parking": 0                // ← Recalculate!
  }
}
```

#### 4. Validate Configuration
```bash
python validate_sheets_config.py --project-id new_project
```

#### 5. Test Data Load
```bash
python3 << 'EOF'
from src.google_sheets_connector import GoogleSheetsConnector
connector = GoogleSheetsConnector()
projects = connector.list_projects()
print(f"Total projects: {len(projects)}")
print(f"Projects: {[p['Project_ID'] for p in projects]}")
EOF
```

**Expected**: Should show 4 projects including `new_project`

#### 6. Update Test Queries (Optional)
**File**: `tests/proof_tester.py`

If you want to include the new project in existing tests:
```python
def test_total_gca(self):
    query = "What is the total GCA for projects Project A, Project Y, Project P (Northside Residential), and New Project?"
    # ... rest of test ...
```

#### 7. Restart and Test
```bash
pkill -f production_mcp_integration.py
bash ./start_web_server.sh
python tests/proof_tester.py
```

### Expected Outcome
- ✅ 4 projects visible in system
- ✅ New project queryable via AI
- ✅ Portfolio totals include new project
- ✅ All tests pass (or updated)

---

## Removing Projects

### Scenario
You need to remove a project from the system

### Step-by-Step Procedure

#### 1. Update Project Manifest
**File**: `config/project_manifest.json`

**Remove entire project object**:
```json
{
  "projects": [
    // Keep these
    { "project_id": "17175_yonge_st", ... },
    { "project_id": "azure_road", ... }
    // REMOVE this one
    // { "project_id": "72_perth", ... }
  ]
}
```

#### 2. Clear Caches
```bash
# Remove project-specific caches
rm cache/test_graph_[SPREADSHEET_ID].json
rm cache/normalized/graph_[SPREADSHEET_ID].json
rm cache/schemas/graph_[SPREADSHEET_ID].json
```

#### 3. Update Ground Truth
**File**: `tests/ground_truth.json`

```json
{
  "projects": {
    // REMOVE this section
    // "72_perth": { ... }
  },
  "portfolio_totals": {
    "total_projects": 2,          // ← Decrement!
    "total_budget": 0,            // ← Recalculate without removed project!
    "total_direct_cost": 0,       // ← Recalculate!
    ...
  }
}
```

#### 4. Update Tests (If Needed)
**File**: `tests/proof_tester.py`

Remove project references from test queries:
```python
# Before:
query = "What is the total GCA for projects Project A, Project Y, and Project P (Northside Residential)?"

# After:
query = "What is the total GCA for projects Project A and Project Y?"
```

#### 5. Restart and Validate
```bash
pkill -f production_mcp_integration.py
bash ./start_web_server.sh
python tests/proof_tester.py
```

### Expected Outcome
- ✅ Project no longer appears in queries
- ✅ Portfolio totals recalculated
- ✅ All tests pass
- ✅ No references to removed project

---

## Updating Ground Truth Data

### When to Update
- ✅ After replacing a spreadsheet
- ✅ When spreadsheet values change
- ✅ After adding/removing projects
- ✅ When tests fail due to data drift

### Automated Extraction Method

**Script**: Create `scripts/extract_ground_truth.py`:

```python
#!/usr/bin/env python3
"""Extract ground truth values from current spreadsheets"""

import sys
import json
sys.path.append('/home/egk/buildbridge-MCP/BuildBridge-MCP')

from src.google_sheets_connector import GoogleSheetsConnector

def extract_ground_truth():
    connector = GoogleSheetsConnector()
    projects = connector.list_projects()
    
    ground_truth = {
        "projects": {},
        "portfolio_totals": {
            "total_projects": len(projects),
            "total_budget": 0,
            "total_direct_cost": 0,
            "total_gca_sf": 0,
            "total_parking": 0
        }
    }
    
    for project in projects:
        project_id = project['Project_ID']
        ground_truth["projects"][project_id] = {
            "name": project.get('Project_Name', ''),
            "total_gca_sf": project.get('Total_GCA_SF', 0),
            "parking_stalls": project.get('Parking_Stalls', 0),
            "total_direct_cost": project.get('Total_Direct_Cost', 0),
            "location": project.get('Location', '')
        }
        
        # Accumulate portfolio totals
        ground_truth["portfolio_totals"]["total_budget"] += project.get('Total_Budget', 0)
        ground_truth["portfolio_totals"]["total_direct_cost"] += project.get('Total_Direct_Cost', 0)
        ground_truth["portfolio_totals"]["total_gca_sf"] += project.get('Total_GCA_SF', 0)
        ground_truth["portfolio_totals"]["total_parking"] += project.get('Parking_Stalls', 0)
    
    print(json.dumps(ground_truth, indent=2))

if __name__ == "__main__":
    extract_ground_truth()
```

**Usage**:
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/extract_ground_truth.py > tests/ground_truth_new.json

# Review the new file
diff tests/ground_truth.json tests/ground_truth_new.json

# If looks good, replace
mv tests/ground_truth_new.json tests/ground_truth.json
```

### Manual Update Method

**Extract values manually**:
```bash
python3 << 'EOF'
from src.google_sheets_connector import GoogleSheetsConnector
import json

connector = GoogleSheetsConnector()
projects = connector.list_projects()

for project in projects:
    print(f"\n{project['Project_ID']}:")
    print(f"  Name: {project.get('Project_Name')}")
    print(f"  GCA: {project.get('Total_GCA_SF')}")
    print(f"  Parking: {project.get('Parking_Stalls')}")
    print(f"  Direct Cost: {project.get('Total_Direct_Cost')}")
    print(f"  Location: {project.get('Location')}")
EOF
```

**Copy values into** `tests/ground_truth.json`

---

## Cache Management

### Understanding Cache Files

**Location**: `cache/` directory

**Types**:
1. **Raw Cache**: `cache/test_graph_[SPREADSHEET_ID].json`
   - Raw data from Google Sheets
   - Includes all tabs and cells
   - Cleared when: Spreadsheet data changes

2. **Normalized Cache**: `cache/normalized/graph_[SPREADSHEET_ID].json`
   - Processed, structured data
   - Optimized for AI queries
   - Cleared when: Data mappings change

3. **Schema Cache**: `cache/schemas/graph_[SPREADSHEET_ID].json`
   - Spreadsheet structure metadata
   - Tab names, column headers
   - Cleared when: Spreadsheet structure changes

### Cache Clearing Commands

```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP

# Clear specific project (by spreadsheet ID)
rm cache/test_graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json
rm cache/normalized/graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json
rm cache/schemas/graph_1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg.json

# Clear all caches (safe - will regenerate)
rm -rf cache/normalized/*
rm -rf cache/schemas/*
rm cache/test_graph_*.json

# Clear EVERYTHING including backups (CAUTION!)
rm -rf cache/*
```

### When to Clear Cache

| Scenario | Clear | Reason |
|----------|-------|--------|
| Spreadsheet data updated | ✅ Yes | Fetch fresh data |
| Project name changed | ✅ Yes | Update metadata |
| Spreadsheet replaced | ✅✅ YES | Critical - old ID cached |
| Tab structure changed | ✅ Yes | Schema changed |
| Data mappings changed | ✅ Yes | Normalization logic changed |
| Just testing queries | ❌ No | Cache is helpful |
| Performance slow | ✅ Maybe | Cache corruption possible |

### Cache Regeneration

**Caches regenerate automatically** when:
- Server starts and cache missing
- Query executed and cache stale
- Explicit refresh triggered

**Manual cache refresh**:
```bash
# Start Python shell
python3

from src.google_sheets_connector import GoogleSheetsConnector
connector = GoogleSheetsConnector()

# Force refresh specific project
connector.clear_cache("72_perth")
data = connector.fetch_project_data("72_perth", force_refresh=True)

print(f"Refreshed {len(data)} rows")
exit()
```

---

## Quick Reference Checklists

### ✅ Changing Project Name Checklist
- [ ] Update `config/project_manifest.json` (keep `project_id` same!)
- [ ] Clear cache files for that project
- [ ] Update `tests/ground_truth.json` (optional)
- [ ] Restart server
- [ ] Run proof tests
- [ ] Verify new name in AI responses

### ✅ Replacing Spreadsheet Checklist
- [ ] Prepare new spreadsheet (share, verify tabs)
- [ ] Get new spreadsheet ID
- [ ] Update `config/project_manifest.json` with new ID
- [ ] Clear ALL cache files
- [ ] Run `validate_sheets_config.py`
- [ ] Extract new ground truth values
- [ ] Update `tests/ground_truth.json`
- [ ] Restart server
- [ ] Run proof tests (expect failures)
- [ ] Iterate ground truth until tests pass
- [ ] Document change in CHANGELOG.md

### ✅ Adding Project Checklist
- [ ] Prepare spreadsheet
- [ ] Add to `config/project_manifest.json`
- [ ] Add to `tests/ground_truth.json`
- [ ] Recalculate portfolio totals
- [ ] Run `validate_sheets_config.py`
- [ ] Update test queries (optional)
- [ ] Restart server
- [ ] Run proof tests
- [ ] Verify 4 projects visible

### ✅ Removing Project Checklist
- [ ] Remove from `config/project_manifest.json`
- [ ] Remove from `tests/ground_truth.json`
- [ ] Recalculate portfolio totals
- [ ] Clear project cache files
- [ ] Update test queries
- [ ] Restart server
- [ ] Run proof tests
- [ ] Verify project gone

---

## Troubleshooting

### "Project not found" Error
**Symptom**: AI says "Project not found" or similar  
**Cause**: `project_id` mismatch or manifest not loaded  
**Fix**:
```bash
# Check manifest syntax
python3 -c "import json; json.load(open('config/project_manifest.json'))"

# Restart server to reload config
pkill -f production_mcp_integration.py
bash ./start_web_server.sh
```

### "Permission denied" for Spreadsheet
**Symptom**: Google Sheets API returns 403  
**Cause**: Service account lacks access  
**Fix**:
1. Open spreadsheet in browser
2. Click "Share"
3. Add: `buildbridge@...iam.gserviceaccount.com`
4. Give "Viewer" or "Editor" permissions
5. Clear cache and retry

### Tests Fail After Spreadsheet Replace
**Symptom**: All values wrong, tests fail  
**Cause**: Ground truth not updated  
**Fix**:
```bash
# Extract actual values
python scripts/extract_ground_truth.py

# Compare and update
diff tests/ground_truth.json tests/ground_truth_new.json

# Use new values
mv tests/ground_truth_new.json tests/ground_truth.json

# Retest
python tests/proof_tester.py
```

### Cache Not Clearing
**Symptom**: Old data still appearing  
**Cause**: Cache files still present or server not restarted  
**Fix**:
```bash
# Nuclear option - clear everything
rm -rf cache/*

# Ensure server restart
pkill -f production_mcp_integration.py
sleep 2
bash ./start_web_server.sh
```

---

## Best Practices

### 1. Always Backup Before Changes
```bash
# Backup manifest
cp config/project_manifest.json config/project_manifest.json.bak

# Backup ground truth
cp tests/ground_truth.json tests/ground_truth.json.bak
```

### 2. Test in Stages
- Test config validation BEFORE full restart
- Test data fetch BEFORE running all tests
- Update ground truth iteratively

### 3. Document Everything
- Use CHANGELOG.md for all spreadsheet changes
- Git commit after each operational change
- Include reason in commit message

### 4. Version Control
```bash
# Commit after operational changes
git add config/ tests/
git commit -m "ops: Replace spreadsheet for 72_perth - Updated estimate"
git push origin feature/proof-testing-framework
```

### 5. Verify with Users
- After major changes, ask users to test queries
- Verify AI responses include correct project names
- Check that calculations remain accurate

---

## Support Contacts

**For Issues**:
- Configuration problems → Check `validate_sheets_config.py` output
- Data issues → Extract ground truth and compare
- Cache issues → Clear everything and restart

**Documentation**:
- Main README: `README.md`
- API Docs: `docs/API_DOCUMENTATION.md`
- Testing Guide: `docs/PROOF_TESTING_README.md`

---

**Last Updated**: October 2, 2025  
**Next Review**: After adding 4th project or significant changes

# Privacy Anonymization Plan
**Date**: October 2, 2025  
**Priority**: CRITICAL - Confidentiality Compliance  
**Status**: In Progress

## Objective
Replace ALL sensitive client and project information with fictitious data while preserving:
- ✅ All cost/budget values (for testing accuracy)
- ✅ All metrics (GCA, parking, areas, etc.)
- ✅ Data structure and relationships
- ✅ Test suite functionality

## Sensitive Information to Anonymize

### 1. Project Names
**Current** → **Anonymized**
- `Project P (Northside Residential)` → `Northside Residential Complex`
- `24019 - Project A` / `6071 Project A` → `Westgate Towers`
- `24021 - Project Y` → `Central Plaza Development`

### 2. Project IDs
**Current** → **Anonymized**
- `72_perth` → `northside_residential`
- `azure_road` → `westgate_towers`
- `17175_yonge_st` → `central_plaza`

### 3. Locations
**Current** → **Anonymized**
- `Toronto, ON` → `Springfield, Ontario`
- `Richmond, British Columbia` → `Riverdale, British Columbia`
- `Project Y Newmarket, Ontario` → `123 Main Street, Lakeside, Ontario`

### 4. Client Names
**Current** → **Anonymized**
- `ABC Development Corp` → `ABC Development Corp`
- `XYZ Properties Ltd` → `XYZ Properties Ltd`
- `Summit Investment Group` → `Summit Investment Group`

### 5. Spreadsheet IDs (New Anonymous Spreadsheets)
**Current** → **New Anonymized Spreadsheets**
- Create 3 new Google Spreadsheets with anonymized data
- Copy structure and values, replace sensitive info
- Update `config/project_manifest.json` with new IDs

## Implementation Steps

### Phase 1: Create Anonymized Spreadsheets (Manual)
1. **Duplicate existing spreadsheets** in Google Drive
2. **Rename spreadsheets**:
   - `Northside Residential Complex - Master Estimate`
   - `Westgate Towers - Master Estimate`
   - `Central Plaza Development - Master Estimate`
3. **Find/Replace in each spreadsheet**:
   - Project names
   - Addresses
   - Client names
   - Any other identifying information
4. **Verify all values preserved**:
   - Budget amounts
   - Direct costs
   - GCA values
   - Parking counts
   - All metrics unchanged

### Phase 2: Update System Configuration (Automated)
1. Update `config/project_manifest.json`
2. Update `tests/ground_truth.json`
3. Update `tests/proof_tester.py` (test queries)
4. Clear all caches
5. Update documentation examples

### Phase 3: Verification
1. Run full test suite
2. Verify all tests pass
3. Test AI queries with new names
4. Confirm no sensitive data exposed

## Detailed Anonymization Mapping

### Project 1: Northside Residential Complex
```json
{
  "original": {
    "project_id": "72_perth",
    "project_name": "Project P (Northside Residential)",
    "location": "Toronto, ON",
    "client": "ABC Development Corp",
    "address": "Project P (Northside Residential)",
    "spreadsheet_name": "Project P (Northside Residential) - Master Estimate"
  },
  "anonymized": {
    "project_id": "northside_residential",
    "project_name": "Northside Residential Complex",
    "location": "Springfield, Ontario",
    "client": "ABC Development Corp",
    "address": "100 Northside Drive",
    "spreadsheet_name": "Northside Residential Complex - Master Estimate"
  },
  "preserve": {
    "total_budget": 0,
    "total_direct_cost": 897836.0,
    "total_gca_sf": 214384,
    "parking_stalls": 31,
    "building_area_metric": 17427,
    "all_division_costs": "unchanged"
  }
}
```

### Project 2: Westgate Towers
```json
{
  "original": {
    "project_id": "azure_road",
    "project_name": "6071 Project A / 24019 - Project A",
    "location": "Richmond, British Columbia",
    "client": "XYZ Properties Ltd",
    "address": "6071 Project A",
    "spreadsheet_name": "24019 - Project A - SKYGRiD Master Estimate"
  },
  "anonymized": {
    "project_id": "westgate_towers",
    "project_name": "Westgate Towers",
    "location": "Riverdale, British Columbia",
    "client": "XYZ Properties Ltd",
    "address": "250 Westgate Boulevard",
    "spreadsheet_name": "Westgate Towers - Master Estimate"
  },
  "preserve": {
    "total_budget": 23981776.0,
    "total_direct_cost": 0,
    "total_gca_sf": 376332,
    "parking_stalls": 0,
    "building_area_imperial": 98515,
    "total_units": 275,
    "all_division_costs": "unchanged"
  }
}
```

### Project 3: Central Plaza Development
```json
{
  "original": {
    "project_id": "17175_yonge_st",
    "project_name": "24021 - Project Y",
    "location": "Project Y Newmarket, Ontario",
    "client": "Summit Investment Group",
    "address": "Project Y",
    "spreadsheet_name": "24021 - Project Y - SKYGRiD Master Estimate"
  },
  "anonymized": {
    "project_id": "central_plaza",
    "project_name": "Central Plaza Development",
    "location": "123 Main Street, Lakeside, Ontario",
    "client": "Summit Investment Group",
    "address": "123 Main Street",
    "spreadsheet_name": "Central Plaza Development - Master Estimate"
  },
  "preserve": {
    "total_budget": 46798403.0,
    "total_direct_cost": 7746848.0,
    "total_gca_sf": 269141,
    "parking_stalls": 197,
    "building_area_metric": 84497,
    "building_area_imperial": 184644,
    "total_units": 208,
    "all_division_costs": "unchanged"
  }
}
```

## Files Requiring Updates

### Configuration Files
- [ ] `config/project_manifest.json` - All project references
- [ ] `tests/ground_truth.json` - Project names and IDs
- [ ] `tests/proof_tester.py` - Test queries
- [ ] `config/vscode_settings_example.json` - MCP config examples

### Documentation Files
- [ ] `README.md` - Example queries
- [ ] `docs/API_DOCUMENTATION.md` - API examples
- [ ] `docs/OPERATIONS_GUIDE.md` - Operation examples
- [ ] `docs/PROOF_TESTING_README.md` - Testing examples
- [ ] `docs/WEEK3_*.md` - All Week 3 documentation
- [ ] `CHANGELOG.md` - Historical references

### Data Files
- [ ] Clear all caches (will regenerate with new data)
- [ ] Backup original `config/project_manifest.json`
- [ ] Backup original `tests/ground_truth.json`

### Scripts
- [ ] `add_project.py` - Example project IDs
- [ ] `validate_sheets_config.py` - No changes needed (generic)

## Spreadsheet Anonymization Checklist

For **EACH** of the 3 spreadsheets, perform these find/replace operations:

### Common Operations (All Tabs)
- [ ] Replace project name/number
- [ ] Replace client name
- [ ] Replace address
- [ ] Replace any contact names
- [ ] Replace any email addresses
- [ ] Replace any phone numbers
- [ ] Check headers for project identifiers
- [ ] Check footers for company names

### Specific Tab Checks
**Project Summary Tab**:
- [ ] Cell B2: Project Name
- [ ] Client name field
- [ ] Location field
- [ ] Any notes with real names

**Exec Summary Tab**:
- [ ] Title/header
- [ ] Client references
- [ ] Any annotations

**GCA Stats Tab**:
- [ ] Building names
- [ ] Address references

**All Cost Breakdown Tabs**:
- [ ] Headers with project identifiers
- [ ] Any vendor names (if present)
- [ ] Any notes referencing real entities

### Verification After Anonymization
- [ ] No real addresses appear
- [ ] No real client names appear
- [ ] No real project names appear
- [ ] All dollar values UNCHANGED
- [ ] All square footage UNCHANGED
- [ ] All parking counts UNCHANGED
- [ ] All metrics UNCHANGED

## Risk Assessment

### High Risk (Must Change)
- ✅ Project names
- ✅ Addresses/locations
- ✅ Client names
- ✅ Project IDs (in system)
- ✅ Spreadsheet IDs (if shared publicly)

### Low Risk (Can Keep)
- ✅ Budget values (not identifying)
- ✅ GCA values (not identifying)
- ✅ Parking counts (not identifying)
- ✅ Division cost breakdowns (generic)
- ✅ Metrics and calculations (generic)

### Must Preserve
- ✅ All test accuracy
- ✅ All calculations
- ✅ All data relationships
- ✅ System functionality

## Post-Anonymization Verification

### Test Suite (Must Pass)
```bash
python tests/proof_tester.py
# Expected: 5/6 or 6/6 tests passing
```

### Manual Queries
```bash
# Query 1: List projects (should show new names)
curl -X POST http://localhost:8000/query \
  -d '{"query": "List all projects"}'

# Query 2: Get budget (should show preserved values)
curl -X POST http://localhost:8000/query \
  -d '{"query": "What is the budget for Northside Residential Complex?"}'

# Query 3: Portfolio totals (should match ground truth)
curl -X POST http://localhost:8000/query \
  -d '{"query": "What is the total budget across all projects?"}'
```

### Documentation Review
- [ ] Search all .md files for "Project P"
- [ ] Search all .md files for "Project A"
- [ ] Search all .md files for "Project Y"
- [ ] Search all .md files for "Castlepoint"
- [ ] Search all .md files for "LDHT"
- [ ] Search all .md files for "Trinity"

## Timeline

### Immediate (Today - Oct 2)
1. ✅ Create anonymization plan (this document)
2. ⏳ Create 3 anonymized spreadsheets in Google Drive
3. ⏳ Update system configuration files

### Next (Oct 3 - Friday)
1. Clear all caches
2. Run test suite
3. Update all documentation
4. Verify no sensitive data remains

## Rollback Plan

If issues arise:
```bash
# Restore original config
cp config/project_manifest.json.bak config/project_manifest.json

# Restore original ground truth
cp tests/ground_truth.json.bak tests/ground_truth.json

# Clear caches
rm -rf cache/*

# Restart server
pkill -f production_mcp_integration.py
bash ./start_web_server.sh
```

## Legal Compliance Notes

⚠️ **CRITICAL**: This anonymization addresses:
- Client confidentiality agreements
- Non-disclosure agreements (NDAs)
- Privacy requirements
- Public repository exposure concerns

✅ **After anonymization**:
- Safe to share repository publicly
- Safe to demo system
- Safe to show in portfolio
- Safe to use in documentation

---

**Status**: Ready to execute  
**Next Step**: Create anonymized spreadsheets in Google Drive  
**Owner**: egk  
**Review Date**: After implementation complete

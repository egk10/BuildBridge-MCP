# Parser Improvements Roadmap

## Overview
This document tracks improvements to the BuildBridge-MCP data parsing system to make it more robust, reliable, and maintainable.

**Last Updated:** October 1, 2025  
**Status:** In Progress

---

## Summary of Issues & Solutions

| Issue | Current State | Better Solution | Priority | Status |
|-------|---------------|-----------------|----------|--------|
| **Hardcoded columns** | ❌ Uses indices [7], [8], [20] | ✅ Search for column headers "GCA (SF)", "GCA (M2)" dynamically | HIGH | 🔄 In Progress |
| **Unit conversion** | ❌ Not implemented | ✅ Add conversion logic with fallback | MEDIUM | ⏳ Pending |
| **Cache staleness** | ❌ Manual refresh only | ✅ Add TTL or webhook from Google Sheets | LOW | ⏳ Pending |
| **Row hardcoding** | ⚠️ Partially (uses labels for some) | ✅ Always use label search, never row numbers | HIGH | 🔄 In Progress |
| **Test parser accuracy** | ⚠️ 20% pass rate | ✅ Better regex patterns to extract AI responses | MEDIUM | ⏳ Pending |

---

## Implementation Checklist

### Phase 1: Dynamic Column Detection (HIGH PRIORITY)

#### 1.1 GCA Stats Tab Parser
- [x] Find "GCA (M2)" column header dynamically in GCA Stats tab
- [x] Find "GCA (SF)" column header dynamically in GCA Stats tab  
- [x] Extract Total GCA values using dynamic column indices
- [x] Remove hardcoded column indices [7], [8]
- [x] Add fallback logic if headers not found
- [x] Test with all 3 projects

#### 1.2 Project Summary Tab Parser
- [ ] Find column headers dynamically instead of using iloc[20]
- [ ] Extract Total_GCA_SF from labeled column
- [ ] Extract Building_Area_Metric from labeled column
- [ ] Extract Building_Area_Imperial from labeled column
- [ ] Extract Parking_Stalls from labeled column
- [ ] Remove all hardcoded column indices
- [ ] Test with all 3 projects

#### 1.3 Parser Utilities
- [x] Create `find_column_by_header()` helper function
- [x] Create `extract_value_by_row_and_column_labels()` helper
- [x] Add header normalization (handle variations like "GCA(SF)", "GCA (SF)", "GCA-SF")
- [x] Add error handling for missing headers
- [x] Add logging for debugging parser issues

---

### Phase 2: Test Parser Improvements (MEDIUM PRIORITY)

#### 2.1 Value Extraction
- [ ] Improve GCA value extraction regex patterns
- [ ] Improve parking stalls extraction patterns
- [ ] Improve cost extraction patterns
- [ ] Handle variations in AI response format
- [ ] Add fallback patterns for different response styles

#### 2.2 Test Robustness
- [ ] Add tolerance for numeric comparisons (±1% default)
- [ ] Better handling of missing values
- [ ] More descriptive error messages
- [ ] Add debug mode to show extraction attempts

---

### Phase 3: Unit Conversion (MEDIUM PRIORITY)

#### 3.1 Core Conversion Logic
- [ ] Create `convert_area()` function (SF ↔ M2)
- [ ] Create `convert_length()` function (ft ↔ m)
- [ ] Create `convert_currency()` function (if needed)
- [ ] Add conversion constants module

#### 3.2 Smart Retrieval
- [ ] Implement `get_gca()` with unit parameter
- [ ] Auto-convert if requested unit not available
- [ ] Prefer stored value over conversion
- [ ] Add metadata about conversion source

---

### Phase 4: Cache Management (LOW PRIORITY)

#### 4.1 Cache Refresh Strategy
- [ ] Add TTL to normalized cache files
- [ ] Implement auto-refresh on startup (optional)
- [ ] Add cache timestamp checking
- [ ] Create manual refresh endpoint

#### 4.2 Cache Monitoring
- [ ] Add cache age display in health check
- [ ] Add "last updated" timestamp to cache files
- [ ] Create cache statistics endpoint
- [ ] Add warning when cache is stale (>24 hours)

#### 4.3 Advanced (Optional)
- [ ] Research Google Sheets webhook/push notifications
- [ ] Implement webhook receiver for sheet updates
- [ ] Add background refresh task
- [ ] Add cache invalidation on sheet change

---

## Current Architecture

### Cache Layers

```
Layer 1: In-memory cache (15 min TTL)
  - Lives in GoogleSheetsConnector._data_cache
  - Expires after 15 minutes
  - Only for read_sheet() calls

Layer 2: Normalized cache files (NO TTL)
  - Lives in cache/normalized/*.json
  - Never expires automatically
  - Must manually refresh with scripts/refresh_manifest_local.py
```

### Data Flow

```
Google Sheets (source of truth)
        ↓
   [Manual refresh script]
        ↓
cache/normalized/*.json (static files)
        ↓
   [MCP Server reads]
        ↓
    AI responses
```

---

## Testing Strategy

After each implementation phase:

1. **Unit Tests**: Test individual parser functions
2. **Integration Tests**: Test full parse flow with sample data
3. **Proof Tests**: Run `tests/proof_tester.py` to validate AI responses
4. **Manual Verification**: Spot-check values against Google Sheets

**Target:** 100% proof test pass rate

---

## Notes & Observations

### Fragile Points Identified
- Column indices assume fixed sheet structure
- No validation if headers change
- No error messages if expected columns missing
- Silent failures return None without explanation

### Design Principles Going Forward
1. **Label-based, not position-based**: Always search for text labels
2. **Defensive parsing**: Assume sheets can change
3. **Clear error messages**: Tell users what's missing
4. **Fallback logic**: Try multiple strategies before giving up
5. **Unit conversion**: Support both metric and imperial
6. **Cache transparency**: Always show age and source

---

## Success Metrics

- [ ] 100% proof test pass rate (currently 20%)
- [ ] Zero hardcoded column/row indices
- [ ] Parser works after column reordering
- [ ] Parser works after column insertion/deletion
- [ ] Clear error messages when parsing fails
- [ ] Sub-second cache read performance maintained

---

## Related Files

- `src/parsers/google_sheet_manifest_parsers.py` - Main parser implementation
- `src/connectors/google_sheets_connector.py` - Google Sheets connector
- `tests/proof_tester.py` - Validation test suite
- `scripts/refresh_manifest_local.py` - Manual cache refresh
- `cache/normalized/*.json` - Cached project data

---

## Change Log

### 2025-10-01 (Evening Update)
- ✅ **Phase 1.1 Complete**: GCA Stats tab now uses dynamic column detection
- ✅ **Phase 1.3 Complete**: Added parser utility functions
  - `find_column_by_header()` - Dynamic column index lookup
  - `extract_value_by_labels()` - Label-based value extraction  
  - `_normalize_header()` - Flexible header matching
- ✅ Parser searches first 10 rows to auto-detect header row
- ✅ Supports header variations: 'GCA(SF)', 'GCA (SF)', 'GCA-SF'
- ✅ All GCA values still correct after refactoring (859,857 SF total)
- 🎯 **Next**: Implement Phase 1.2 (Project Summary tab dynamic detection)

### 2025-10-01
- ✅ Fixed: Load project data from normalized cache instead of live sheets
- ✅ Fixed: Extract Total_GCA_SF from GCA Stats tab instead of Project Summary
- ✅ Updated: Added Total_GCA_SF, Total_Budget, Total_Direct_Cost to AI prompts
- ✅ Result: AI now sees all 3 projects and returns correct GCA values (859,857 SF total)
- 📝 Created: This roadmap document

---

## Next Actions

**Immediate Priority:**
1. Implement dynamic column detection for GCA Stats tab
2. Implement dynamic column detection for Project Summary tab
3. Test all parsers with current data
4. Improve test parser extraction patterns
5. Achieve 100% proof test pass rate

# Spreadsheet Anonymization Checklist
**Date:** October 3, 2025  
**Priority:** CRITICAL - Manual Data Editing Required  
**Status:** 🔴 NOT STARTED

---

## 📋 Overview

You need to manually edit **3 Google Spreadsheets** to replace ALL sensitive information with anonymized data. The system configuration has been updated to use single-letter project IDs (P, A, Y), but the actual spreadsheet content still contains real names, addresses, and client information.

**⚠️ IMPORTANT:** 
- Keep ALL numeric values unchanged (budgets, costs, GCA, parking, etc.)
- Keep ALL formulas unchanged
- ONLY change text-based identifying information

---

## 🎯 Quick Reference: What to Change

### Project P (Project P (Northside Residential))
| Current (REAL) | New (ANONYMIZED) |
|----------------|------------------|
| Project P (Northside Residential) | Northside Residential Complex |
| Toronto, ON | Springfield, Ontario |
| Project P | 100 Northside Drive |
| ABC Development Corp | ABC Development Corp |

### Project Y (Project Y)
| Current (REAL) | New (ANONYMIZED) |
|----------------|------------------|
| 24021 - Project Y | Central Plaza Development |
| Project Y | 123 Main Street |
| Newmarket, Ontario | Lakeside, Ontario |
| Summit Investment Group | Summit Investment Group |

### Project A (Project A)
| Current (REAL) | New (ANONYMIZED) |
|----------------|------------------|
| 6071 Project A | Westgate Towers |
| 24019 - Project A | Westgate Towers |
| Richmond, British Columbia | Riverdale, British Columbia |
| XYZ Properties Ltd | XYZ Properties Ltd |

---

## 📝 Detailed Checklist

### Spreadsheet 1: Project P (Project P (Northside Residential))
**Spreadsheet ID:** `1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k`  
**Link:** https://docs.google.com/spreadsheets/d/1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k/edit

#### Tab: Project Summary
- [ ] **Cell B2** (or title area): Change project name
  - From: "Project P (Northside Residential)"
  - To: "Northside Residential Complex"
  
- [ ] **Location field**: Change address
  - From: "Project P" / "Toronto, ON"
  - To: "100 Northside Drive, Springfield, Ontario"
  
- [ ] **Client field**: Change client name
  - From: "ABC Development Corp"
  - To: "ABC Development Corp"

- [ ] **Search entire tab** (Ctrl+F):
  - [ ] Search "Project P" → Replace with "Northside"
  - [ ] Search "72" (be careful with numbers!) → Replace "Project P" with "Northside"
  - [ ] Search "Castlepoint" → Replace with "ABC Development"
  - [ ] Search "Numa" → Replace with "Corp"
  - [ ] Search "Toronto" → Replace with "Springfield"

#### Tab: Exec Summary
- [ ] Header/title: Change project name
- [ ] Any client references: Change to "ABC Development Corp"
- [ ] Any location references: Change to "Springfield, Ontario"

#### Tab: GCA Stats
- [ ] Building name: Change if present
- [ ] Address references: Change to "100 Northside Drive"
- [ ] Any notes with real names: Anonymize

#### Tab: Above Grade Detail (AG - A)
- [ ] Header: Update project name
- [ ] Any descriptions with location: Anonymize

#### Tab: Parking
- [ ] Header: Update project name
- [ ] Location references: Anonymize

#### Verification
- [ ] Search for "Project P" - should find 0 results
- [ ] Search for "Castlepoint" - should find 0 results
- [ ] Search for "72" - verify only in numeric values (like $72.00), not text
- [ ] All dollar amounts unchanged
- [ ] All square footage values unchanged
- [ ] All parking counts unchanged

---

### Spreadsheet 2: Project Y (Project Y)
**Spreadsheet ID:** `1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU`  
**Link:** https://docs.google.com/spreadsheets/d/1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU/edit

#### Tab: Project Summary
- [ ] **Project name field**: Change
  - From: "24021 - Project Y" or "Project Y"
  - To: "Central Plaza Development"
  
- [ ] **Location field**: Change address
  - From: "Project Y, Newmarket, Ontario"
  - To: "123 Main Street, Lakeside, Ontario"
  
- [ ] **Client field**: Change client name
  - From: "Summit Investment Group"
  - To: "Summit Investment Group"

- [ ] **Project number**: Change
  - From: "24021"
  - To: "CPD-001" (Central Plaza Development)

- [ ] **Search entire tab** (Ctrl+F):
  - [ ] Search "Project Y" → Replace with "Main Street"
  - [ ] Search "17175" → Replace with "123"
  - [ ] Search "24021" → Replace with "CPD-001"
  - [ ] Search "Trinity" → Replace with "Summit"
  - [ ] Search "Coptic" → Replace with "Investment"
  - [ ] Search "Foundation" → Replace with "Group"
  - [ ] Search "Newmarket" → Replace with "Lakeside"

#### Tab: Exec Summary
- [ ] Header: Update to "Central Plaza Development"
- [ ] Project number: Change to "CPD-001"
- [ ] Client: "Summit Investment Group"
- [ ] Location: "Lakeside, Ontario"

#### Tab: GCA Stats
- [ ] Building name: "Central Plaza Development"
- [ ] Address: "123 Main Street"
- [ ] Any unit names with "Project Y": Change to "Plaza"

#### Tab: Below Grade 1 Detail (BG1)
- [ ] Header: Update project name
- [ ] Any location references: Anonymize

#### Verification
- [ ] Search for "Project Y" - should find 0 results
- [ ] Search for "17175" - should find 0 results
- [ ] Search for "24021" - should find 0 results
- [ ] Search for "Trinity" - should find 0 results
- [ ] Search for "Coptic" - should find 0 results
- [ ] Search for "Newmarket" - should find 0 results
- [ ] Total budget: $46,798,403 (UNCHANGED)
- [ ] Total direct cost: $7,746,848 (UNCHANGED)
- [ ] Total GCA: 269,141 SF (UNCHANGED)
- [ ] Parking stalls: 197 (UNCHANGED)

---

### Spreadsheet 3: Project A (Project A)
**Spreadsheet ID:** `1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg`  
**Link:** https://docs.google.com/spreadsheets/d/1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg/edit

#### Tab: Project Summary
- [ ] **Project name field**: Change
  - From: "24019 - Project A" or "6071 Project A"
  - To: "Westgate Towers"
  
- [ ] **Location field**: Change address
  - From: "6071 Project A, Richmond, British Columbia"
  - To: "250 Westgate Boulevard, Riverdale, British Columbia"
  
- [ ] **Client field**: Change client name
  - From: "XYZ Properties Ltd"
  - To: "XYZ Properties Ltd"

- [ ] **Project number**: Change
  - From: "24019"
  - To: "WGT-001" (Westgate Towers)

- [ ] **Search entire tab** (Ctrl+F):
  - [ ] Search "Project A" → Replace with "Westgate"
  - [ ] Search "6071" → Replace with "250"
  - [ ] Search "24019" → Replace with "WGT-001"
  - [ ] Search "LDHT" → Replace with "XYZ Properties"
  - [ ] Search "Holdings" → Replace with "Ltd"
  - [ ] Search "Richmond" → Replace with "Riverdale"

#### Tab: Exec Summary
- [ ] Header: Update to "Westgate Towers"
- [ ] Project number: Change to "WGT-001"
- [ ] Client: "XYZ Properties Ltd"
- [ ] Location: "Riverdale, British Columbia"

#### Tab: GCA Stats
- [ ] Building name: "Westgate Towers"
- [ ] Address: "250 Westgate Boulevard"
- [ ] Any unit names with "Project A": Change to "Westgate"

#### Tab: AG - A (Above Grade A)
- [ ] Header: Update project name
- [ ] Any location references: Anonymize

#### Tab: AG - B (Above Grade B)
- [ ] Header: Update project name
- [ ] Any location references: Anonymize

#### Tab: AG - C (Above Grade C)
- [ ] Header: Update project name
- [ ] Any location references: Anonymize

#### Tab: Parking
- [ ] Header: Update project name (if parking tab exists)

#### Verification
- [ ] Search for "Project A" - should find 0 results
- [ ] Search for "6071" - should find 0 results
- [ ] Search for "24019" - should find 0 results
- [ ] Search for "LDHT" - should find 0 results
- [ ] Search for "Richmond" (be careful, could be in "British Columbia Richmond") - replace specific instances
- [ ] Total budget: $23,981,776 (UNCHANGED)
- [ ] Total direct cost: $0 (UNCHANGED)
- [ ] Total GCA: 376,332 SF (UNCHANGED)
- [ ] Parking stalls: 0 (UNCHANGED)

---

## ✅ Final Verification Steps

### After editing ALL 3 spreadsheets:

1. **Cross-check all spreadsheets:**
   - [ ] Open all 3 spreadsheets side-by-side
   - [ ] Search each for original names (Project P, Project Y, Project A, etc.)
   - [ ] Verify 0 results for sensitive terms

2. **Verify numeric integrity:**
   - [ ] Project P: Total GCA = 214,384 SF ✅
   - [ ] Project Y: Total GCA = 269,141 SF ✅
   - [ ] Project A: Total GCA = 376,332 SF ✅
   - [ ] Portfolio Total Budget = $70,780,179 ✅

3. **Test the system:**
   ```bash
   # Regenerate cache with anonymized data
   cd /home/egk/buildbridge-MCP/BuildBridge-MCP
   rm -rf cache/normalized/*
   python scripts/refresh_manifest_local.py --force
   
   # Rename cache files to uppercase
   cd cache/normalized
   mv a.json A.json
   mv p.json P.json
   mv y.json Y.json
   
   # Restart server
   pkill -f production_mcp_integration
   nohup bash start_web_server.sh > server_runtime.log 2>&1 &
   
   # Run tests
   sleep 5
   python tests/proof_tester.py
   ```

4. **Verify queries return anonymized data:**
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "List all projects", "type": "ai_query"}' | jq '.data.ai_response'
   ```
   - Should see: "Northside Residential Complex", "Central Plaza Development", "Westgate Towers"
   - Should NOT see: "Project P", "Project Y", "Project A", "Castlepoint", "Trinity", "LDHT"

---

## 🚨 Common Mistakes to Avoid

1. **Changing numeric values:**
   - ❌ DON'T change: $46,798,403 → $46,000,000
   - ✅ KEEP: All exact dollar amounts
   - ✅ KEEP: All square footage
   - ✅ KEEP: All unit counts

2. **Changing formulas:**
   - ❌ DON'T modify: =SUM(B2:B50)
   - ✅ KEEP: All formulas unchanged
   - ✅ UPDATE: Only text in cells, not formulas

3. **Incomplete replacements:**
   - ❌ Changing "Project Y" to "123 Project Y"
   - ✅ Must change BOTH: "123 Main Street"

4. **Case sensitivity:**
   - Search for: "Project P", "PERTH", "perth"
   - Search for: "Project A", "AZURE", "azure"
   - Search for: "Project Y", "YONGE", "yonge"

---

## 📊 Progress Tracker

### Spreadsheet 1 (Project P):
- [ ] Tab: Project Summary
- [ ] Tab: Exec Summary
- [ ] Tab: GCA Stats
- [ ] Tab: Above Grade Detail
- [ ] Tab: Parking
- [ ] Verification complete
- [ ] **Status:** ⬜ Not Started

### Spreadsheet 2 (Project Y):
- [ ] Tab: Project Summary
- [ ] Tab: Exec Summary
- [ ] Tab: GCA Stats
- [ ] Tab: Below Grade 1 Detail
- [ ] Verification complete
- [ ] **Status:** ⬜ Not Started

### Spreadsheet 3 (Project A):
- [ ] Tab: Project Summary
- [ ] Tab: Exec Summary
- [ ] Tab: GCA Stats
- [ ] Tab: AG - A
- [ ] Tab: AG - B
- [ ] Tab: AG - C
- [ ] Tab: Parking
- [ ] Verification complete
- [ ] **Status:** ⬜ Not Started

### System Testing:
- [ ] Cache regenerated
- [ ] Tests passing (5/6 or better)
- [ ] Queries return anonymized names
- [ ] **Status:** ⬜ Not Started

---

## ⏱️ Estimated Time

- **Spreadsheet 1 (P):** ~15 minutes
- **Spreadsheet 2 (Y):** ~20 minutes (more tabs)
- **Spreadsheet 3 (A):** ~25 minutes (most tabs)
- **Verification & Testing:** ~15 minutes
- **Total:** ~75 minutes (1.25 hours)

---

## 🎯 Success Criteria

✅ **Complete when:**
1. All 3 spreadsheets edited and verified
2. No sensitive terms found in any spreadsheet
3. All numeric values preserved
4. Cache regenerated successfully
5. Tests passing with anonymized names
6. System queries return only anonymized data

🔒 **Privacy Compliance Achieved!**

---

**Last Updated:** October 3, 2025 - 10:35 AM  
**Status:** 🔴 **READY TO BEGIN - MANUAL EDITING REQUIRED**  
**Next Action:** Open first spreadsheet and start editing

Good luck! Take your time and double-check each change. 💪

# Week 3 Quick Checklist ✅

**Goal:** 7/7 tests (117% coverage) + User docs  
**Dates:** Oct 3-9, 2025

---

## Monday, Oct 3 - Production Monitoring

### Morning: Health Check
- [ ] Check server logs (no errors?)
- [ ] Test `/health` endpoint
- [ ] Test `/api/projects` endpoint  
- [ ] Verify Chat V2 working (5+ button clicks)

### Afternoon: Metrics
- [ ] Count total queries since launch
- [ ] Identify common query patterns
- [ ] Track response times
- [ ] Create `docs/PRODUCTION_METRICS_OCT3.md`

---

## Tuesday, Oct 4 - User Feedback

### Morning: Categorize Queries
- [ ] Single project queries (count, %)
- [ ] Cross-project comparisons (count, %)
- [ ] Portfolio calculations (count, %)
- [ ] Division cost queries (count, %)
- [ ] "What-if" queries (count, %)

### Afternoon: Analysis
- [ ] Top 5 most requested query types?
- [ ] Any failed/poor responses?
- [ ] Would formula-awareness help?
- [ ] Create `docs/WEEK3_FEEDBACK_SUMMARY.md`

---

## Wednesday, Oct 5 - Test 7 Prep

### Morning: Ground Truth
- [ ] Open Project P spreadsheet → Extract Division 03 cost
- [ ] Open Project Y spreadsheet → Extract Division 03 cost
- [ ] Open Project A spreadsheet → Extract Division 03 cost
- [ ] Calculate unit costs (cost / GCA SF)
- [ ] Calculate ratios (cost / total budget)
- [ ] Update `tests/ground_truth.json`

### Afternoon: Context Enhancement
- [ ] Check if division costs in formatted context
- [ ] If not, enhance `google_sheet_manifest_parsers.py`
- [ ] Verify division data accessible to AI

---

## Thursday, Oct 6 - Test 7 Implementation

### Morning: Code
- [ ] Add `test_division_comparison()` to `proof_tester.py`
- [ ] Add extraction helper methods
- [ ] Update test runner to include Test 7
- [ ] Initial test run

### Afternoon: Refinement
- [ ] Run Test 7: `pytest tests/proof_tester.py::test_division_comparison -v`
- [ ] If fails, refine query wording
- [ ] Adjust extraction patterns
- [ ] Run full suite: `pytest tests/proof_tester.py -v`
- [ ] **Target:** 7/7 tests passing ✅

---

## Friday, Oct 7 - Documentation

### Morning: Query Patterns
- [ ] Create `docs/QUERY_PATTERNS.md`
- [ ] Document 5 query categories with examples
- [ ] Add best practices section
- [ ] Add common mistakes section

### Afternoon: UI Enhancements
- [ ] Add tooltips to project buttons
- [ ] Add "Pro Tips" section to sidebar
- [ ] Add rotating example query hints
- [ ] Test UI improvements

---

## End of Week Checklist

### Documentation Created:
- [ ] `docs/PRODUCTION_METRICS_OCT3.md`
- [ ] `docs/WEEK3_FEEDBACK_SUMMARY.md`
- [ ] `docs/QUERY_PATTERNS.md`
- [ ] `docs/WEEK3_DAILY_NOTES.md`

### Code Updated:
- [ ] `tests/ground_truth.json` (Test 7 data)
- [ ] `tests/proof_tester.py` (Test 7 implementation)
- [ ] `static/chat_interface_v2.html` (UI enhancements)
- [ ] `src/parsers/google_sheet_manifest_parsers.py` (if needed)

### Success Metrics:
- [ ] ✅ 7/7 tests passing
- [ ] ✅ 117% test coverage
- [ ] ✅ Zero production errors
- [ ] ✅ Query guide complete

---

## Quick Commands

```bash
# Check server logs
tail -f logs/server.log | grep -i error

# Run full test suite
pytest tests/proof_tester.py -v

# Run Test 7 only
pytest tests/proof_tester.py::test_division_comparison -v

# Test a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare Concrete costs across all projects"}'

# Check server health
curl http://localhost:8000/health
```

---

**Status:** 🚀 Ready to start!  
**Next:** Monday morning - Production monitoring

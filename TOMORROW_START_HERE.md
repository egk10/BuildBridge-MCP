# Quick Start Guide - October 2, 2025

## 🎯 Today's Mission: Reach 80-100% Test Pass Rate

**Current Status**: 50% (3/6 tests passing)  
**Branch**: `feature/proof-testing-framework`  
**Last Commit**: `bbf95c5` - 50% milestone achieved

---

## Quick Setup (2 minutes)

```bash
# 1. Navigate to project
cd /home/egk/buildbridge-MCP/BuildBridge-MCP

# 2. Activate virtual environment
source buildbridge_venv/bin/activate

# 3. Verify server is running
curl -s http://localhost:8000/health | head -5

# 4. Run current tests to see baseline
python tests/proof_tester.py
```

---

## Task 1: Portfolio Totals (30 min) 🎯

**Goal**: Fix Test 5 → 66% pass rate

### Investigation
```bash
# See what AI returns for portfolio query
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Give me the portfolio totals across all projects: total budget, total direct cost, total GCA","type":"ai_query","parameters":{"include_data_context":true}}' \
  | python3 -m json.tool | head -40

# Check expected values
python3 -c "import json; gt=json.load(open('tests/ground_truth.json')); print('Expected:', json.dumps(gt['portfolio_totals'], indent=2))"
```

### Expected Values
- Total Budget: $70,780,179
- Total Direct Cost: $8,644,684
- Total GCA: 859,857 SF

### Current Issue
- Total Budget: Not found
- Direct Cost: $46,798,403 (wrong!)
- GCA: Not checked

### Fix
Apply section-based extraction to `test_portfolio_totals()` in `tests/proof_tester.py`

---

## Task 2: Parking Query Wording (30 min) 🎯

**Goal**: Fix Test 2 → 83% pass rate

### Try New Query Wording
```bash
# Test 1: More specific
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"List the exact number of parking stalls for each project: 72 Perth Avenue, 17175 Yonge St, and Azure Road. For each project, provide only the parking stall count.","type":"ai_query","parameters":{"include_data_context":true}}' \
  | python3 -m json.tool | grep -A 5 -B 5 "stall"

# Test 2: Direct question
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"How many parking stalls does 72 Perth Avenue have? How many does 17175 Yonge St have? How many does Azure Road have?","type":"ai_query","parameters":{"include_data_context":true}}' \
  | python3 -m json.tool | grep -A 5 -B 5 "stall"
```

### Expected Values
- 72 Perth: 31 stalls
- Yonge St: 220 stalls
- Azure Road: 282 stalls

### Current Issue
AI returns: "Progress Percentage... Budget Status..." instead of stall counts

### Fix Options
1. Change query wording in `test_parking_stalls()`
2. Or: Update prompts to always include parking in formatted context

---

## Task 3: Debug 72 Perth Data Context (1 hour) 🔍

**Goal**: Fix Test 3 → 100% pass rate

### Investigation Steps

```bash
# 1. Verify cache has data
python3 -c "import json; d=json.load(open('cache/normalized/72_perth.json')); print('Cost:', d['project']['Total_Direct_Cost'], 'Parking:', d['project']['Parking_Stalls'])"

# 2. Check if 72 Perth loads in context
grep -n "72_perth\|72 Perth" src/prompts/construction_prompts.py

# 3. Check formatted context
grep -n "format_project_context\|Total_Direct_Cost\|Parking" src/prompts/construction_prompts.py
```

### Current Issue
- AI says: "I don't have budget information for '72 Perth Avenue'"
- But cache has: $897,836 direct cost, 31 parking stalls
- Yonge and Azure work fine (AI provides their data)

### Expected Root Cause
Likely one of:
1. 72 Perth not being loaded into context
2. Cost/parking fields not included in formatted context
3. AI filtering out 72 Perth for some reason

### Fix
Update `src/prompts/construction_prompts.py` to ensure:
- All projects included in context
- Parking stalls in formatted output
- Cost fields in formatted output

---

## Files to Review

### Test Files
- `tests/proof_tester.py` - Main test suite
- `tests/ground_truth.json` - Expected values
- `tests/proof_test_results.json` - Latest results

### Source Files to Investigate
- `src/prompts/construction_prompts.py` - **KEY FILE** for AI formatting
- `src/services/query_processor.py` - Context loading
- `src/parsers/google_sheet_manifest_parsers.py` - Data parsing

### Cache Files
- `cache/normalized/72_perth.json` - 72 Perth data
- `cache/normalized/17175_yonge_st.json` - Yonge data
- `cache/normalized/azure_road.json` - Azure data

### Documentation
- `docs/SESSION_SUMMARY_2025-10-01.md` - Yesterday's summary
- `docs/PHASE_2_PROGRESS.md` - Detailed progress report
- `docs/PARSER_IMPROVEMENTS_ROADMAP.md` - Overall roadmap

---

## Success Criteria

### Task 1 Complete ✅
- [ ] Portfolio totals test passes
- [ ] Pass rate: 66% (4/6 tests)
- [ ] Budget, cost, and GCA extracted correctly

### Task 2 Complete ✅
- [ ] Parking stalls test passes
- [ ] Pass rate: 83% (5/6 tests)
- [ ] All 3 projects return stall counts

### Task 3 Complete ✅
- [ ] Direct costs test passes
- [ ] Pass rate: 100% (6/6 tests)
- [ ] 72 Perth data included in AI responses

### Session Complete 🎉
- [ ] All 6 tests passing consistently
- [ ] Documentation updated
- [ ] Changes committed and pushed
- [ ] Ready to demo or merge PR

---

## Quick Commands Reference

### Run Tests
```bash
python tests/proof_tester.py
```

### Test Single Query
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"YOUR QUERY HERE","type":"ai_query","parameters":{"include_data_context":true}}' \
  | python3 -m json.tool
```

### Check Ground Truth
```bash
python3 -c "import json; gt=json.load(open('tests/ground_truth.json')); print(json.dumps(gt, indent=2))"
```

### Git Commands
```bash
git status
git add -A
git commit -m "Your message"
git push origin feature/proof-testing-framework
```

---

## Remember

✅ **What's Working**:
- Section-based extraction (proven with GCA test)
- Extraction patterns are correct
- Cache has all the data

⚠️ **What's Not**:
- AI response consistency
- Query formulations
- Data context inclusion

🎯 **Focus**: 
- Not the extraction patterns (they work!)
- Focus on AI behavior and prompts

---

## Energy Level Estimation

- Task 1: ☕ Low energy (investigation + pattern application)
- Task 2: ☕☕ Medium energy (testing query variations)
- Task 3: ☕☕☕ Higher energy (debugging, prompt engineering)

**Recommendation**: Do tasks in order. If energy is low, Task 1 alone gets us to 66%!

---

**Good luck! You've got this! 🚀**

**Yesterday we doubled the pass rate. Today we finish the job!** 💪

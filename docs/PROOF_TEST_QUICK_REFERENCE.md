# Proof Test Plan - Quick Reference

## 📦 What Was Created

### Documentation
- ✅ **`docs/PROOF_TEST_PLAN.md`** - Comprehensive 200+ line testing plan with:
  - Test objectives and strategy
  - 8 test categories with 20+ test queries
  - Ground truth preparation steps
  - Automated validation scripts
  - Success criteria and metrics
  - Execution instructions

### Scripts
- ✅ **`scripts/create_ground_truth.py`** - Extracts current Google Sheets data to JSON
- ✅ **`tests/proof_tester.py`** - Automated Python test suite (300+ lines)
- ✅ **`tests/manual_curl_tests.sh`** - Interactive CURL test script (executable)
- ✅ **`tests/README_PROOF_TESTS.md`** - Testing documentation

## 🎯 Test Coverage

### Projects Being Tested
1. **Project P (Northside Residential)** (toronto)
   - GCA: 205 SF
   - Parking: 31 stalls
   - Direct Cost: $897,836

2. **Project Y** (location TBD)
   - Full metrics from Google Sheets

3. **Project A** (location TBD)
   - Full metrics from Google Sheets

### 20+ Test Queries Created

#### Category 1: Basic Info (3 tests)
- Total GCA for all projects
- Parking stalls per project
- Project locations

#### Category 2: Budget Analysis (3 tests)
- Total Direct Cost accuracy
- Budget comparison
- Cost per square foot

#### Category 3: Material Costs (3 tests)
- Concrete costs for Project Y
- Steel costs comparison
- Sitework costs

#### Category 4: Building Metrics (3 tests)
- Area (metric vs imperial)
- Functional units
- Client information

#### Category 5: Aggregations (3 tests)
- Portfolio totals
- Average metrics
- Largest/smallest comparisons

#### Category 6: Division Costs (2 tests)
- Below grade costs
- CSI division breakdowns

#### Category 7: Dates (1 test)
- Budget update dates

#### Category 8: Complex Queries (2 tests)
- Best value analysis
- Resource intensity calculations

## 🚀 How to Use

### Step 1: Generate Ground Truth
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/create_ground_truth.py
```

**Output**: `tests/ground_truth.json` with current Google Sheets values

### Step 2: Start MCP Server
```bash
./start_buildbridge.sh
```

### Step 3: Run Automated Tests
```bash
python tests/proof_tester.py
```

**Output**: 
- Console report with pass/fail status
- `tests/proof_test_results.json` with detailed results

### Step 4: Optional Manual Testing
```bash
cd tests
./manual_curl_tests.sh
```

**Output**: Interactive CURL queries with formatted JSON responses

## 📊 Expected Test Results

```
====================================================================
🏗️  BuildBridge-MCP Proof Testing Suite
====================================================================
Server: http://localhost:8000
Ground Truth: tests/ground_truth.json
Projects: 3

✅ Server is healthy
   AI Service: Enabled
   Model: gpt-3.5-turbo

🧪 Test 1: Total GCA Query
  ✅ PASSED

🧪 Test 2: Parking Stalls Query
  ✅ PASSED

🧪 Test 3: Total Direct Cost Query
  ✅ PASSED

🧪 Test 4: Project Locations Query
  ✅ PASSED

🧪 Test 5: Portfolio Totals Query
  ✅ PASSED

====================================================================
📊 Test Summary
====================================================================
Total Tests: 5
Passed: 5
Failed: 0
Success Rate: 100.0%
Total Time: 15.3s

📝 Detailed results saved to: tests/proof_test_results.json

🎉 ALL TESTS PASSED! Query accuracy validated successfully.
```

## 🎨 Test Query Examples

### Example 1: GCA Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total GCA for projects Project A, Project Y, and Project P (Northside Residential)?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Response**: Includes GCA values for all 3 projects matching ground truth

### Example 2: Cost Analysis
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the Total Direct Cost for Project P (Northside Residential), Project Y, and Project A?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Response**: 
- Project P (Northside Residential): $897,836
- Other projects: Values from ground truth

### Example 3: Parking Comparison
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many parking stalls does each project have?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Response**: 
- Project P (Northside Residential): 31 stalls
- Other projects: Values from ground truth

## ✅ Success Criteria

### Accuracy Thresholds
- ✅ Project names, locations: 100% exact match
- ✅ Costs and areas: Within 1% tolerance
- ✅ Parking counts: Exact match
- ✅ Overall success rate: > 95%

### Performance Benchmarks
- ✅ Response time: < 5 seconds per query
- ✅ No server errors
- ✅ All 3 projects included in responses

## 🔍 Ground Truth Structure

```json
{
  "generated_at": "2025-10-01T00:00:00",
  "projects": {
    "72_perth": {
      "name": "Project P (Northside Residential)",
      "location": "Toronto, ON",
      "client": "ABC Development Corp",
      "total_budget": 0.0,
      "total_direct_cost": 897836.0,
      "building_area_metric": 17427.0,
      "total_gca_sf": 205.0,
      "parking_stalls": 31,
      "parking_total": 31
    },
    "17175_yonge_st": { ... },
    "azure_road": { ... }
  },
  "portfolio_totals": {
    "total_projects": 3,
    "total_budget": sum,
    "total_direct_cost": sum,
    "total_gca_sf": sum,
    "total_parking": sum
  }
}
```

## 📁 File Structure

```
BuildBridge-MCP/
├── docs/
│   └── PROOF_TEST_PLAN.md          ← Main testing documentation
├── scripts/
│   └── create_ground_truth.py      ← Ground truth generator
├── tests/
│   ├── proof_tester.py             ← Automated test suite
│   ├── manual_curl_tests.sh        ← Manual CURL tests
│   ├── README_PROOF_TESTS.md       ← Testing guide
│   ├── ground_truth.json           ← Generated ground truth
│   └── proof_test_results.json     ← Test results (generated)
└── cache/
    └── normalized/
        ├── 72_perth.json           ← Source data
        ├── 17175_yonge_st.json
        └── azure_road.json
```

## 🎯 Next Steps

1. **Generate ground truth** from your Google Sheets
   ```bash
   python scripts/create_ground_truth.py
   ```

2. **Start the server** if not running
   ```bash
   ./start_buildbridge.sh
   ```

3. **Run automated tests** to validate accuracy
   ```bash
   python tests/proof_tester.py
   ```

4. **Review results** and compare with ground truth
   ```bash
   cat tests/proof_test_results.json | jq '.'
   ```

5. **Run manual tests** for interactive exploration (optional)
   ```bash
   ./tests/manual_curl_tests.sh
   ```

## 📚 Documentation References

- **Full Plan**: `docs/PROOF_TEST_PLAN.md` - Complete testing strategy
- **Test Guide**: `tests/README_PROOF_TESTS.md` - How to use the tests
- **AI Usage**: `docs/AI_INTEGRATION_USAGE_GUIDE.md` - AI service details
- **Interaction**: `docs/INTERACTION_GUIDE.md` - Server usage guide

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Ground truth not found | Run `python scripts/create_ground_truth.py` |
| Server not responding | Start with `./start_buildbridge.sh` |
| Tests failing | Regenerate ground truth after data updates |
| AI service disabled | Check `.env` for `OPENAI_API_KEY` |

## 🎉 Ready to Test!

Your BuildBridge-MCP proof testing suite is complete and ready to use. The system will:

1. ✅ Query your live MCP server
2. ✅ Extract values from AI responses
3. ✅ Compare against Google Sheets ground truth
4. ✅ Report accuracy metrics
5. ✅ Generate detailed test results

**Start testing now**: `python scripts/create_ground_truth.py && python tests/proof_tester.py`

---

**Created**: October 1, 2025  
**Status**: ✅ Ready for Execution  
**Coverage**: 20+ test queries across 8 categories

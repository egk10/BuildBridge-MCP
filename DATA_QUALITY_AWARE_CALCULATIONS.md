# Data Quality Aware Calculations - Quick Reference

**Status:** ✅ Production Ready (October 2, 2025)  
**Feature:** AI performs calculations while detecting and reporting data quality issues  

---

## What This Does

BuildBridge AI now acts as both a **calculator** AND a **data quality consultant** when processing portfolio queries.

### Before
```
Query: "Add up total budget"
Response: "Here are the values: Project A=$10M, Project B=$20M..."
Result: ❌ No calculation, no insights
```

### After
```
Query: "Add up total budget"
Response: 
  ✅ Total: $30M (calculated)
  ⚠️ Project A has #DIV/0! errors in unit costs
  📋 Recommendation: Check GCA Stats tab for missing area values
Result: ✅ Calculation + Data Quality Audit + Actionable Guidance
```

---

## How It Works

### Automatic Detection

When you ask calculation questions, AI automatically:

1. **Detects Intent**
   - Keywords: "calculate", "add up", "sum", "total", "aggregate"
   - Phrases: "across all projects", "for all projects", "give me the total"

2. **Checks Data Quality**
   - Spreadsheet errors: #DIV/0!, #ERROR!, #N/A, #VALUE!, #REF!
   - Anomalies: $0 budgets with spending, unusual values
   - Missing data: Empty critical fields, incomplete calculations

3. **Performs Calculation**
   - Shows work: "$0 + $46,798,403 + $23,981,776 = $70,780,179"
   - Marks caveats: "CAUTION: derived metrics have errors"
   - Provides totals clearly

4. **Gives Recommendations**
   - Root causes: "Zero GCA area causing division by zero"
   - Locations: "Check GCA Stats tab for 17175 Yonge St"
   - Action items: "Verify area calculations, use preliminary estimates"

---

## Example Queries

### Portfolio Totals
```
Query: "Add up total budget and total direct cost across all projects"

Response:
✅ Total Budget: $70,780,179
✅ Total Direct Cost: $8,644,684
⚠️ Issues: 72 Perth has $0 budget but $897K spent
```

### Cross-Project Comparison
```
Query: "Compare Concrete Placing costs across all projects"

Response:
17175 Yonge St: $XXX ($/SF: $XX, Ratio: X.XX%)
Azure Road: $YYY ($/SF: $YY, Ratio: Y.YY%)
⚠️ Note: 72 Perth missing Division 03 breakdown
```

### Unit Cost Analysis
```
Query: "What is the average cost per square foot across projects?"

Response:
✅ Average: $XXX/SF
⚠️ Azure Road has no SF data - excluded from average
📋 Check: Verify if SF data available in future revisions
```

---

## Data Quality Checks Performed

### Spreadsheet Errors
- `#DIV/0!` - Division by zero (usually missing area/denominator)
- `#ERROR!` - General calculation error
- `#N/A` - Not available / lookup failed
- `#VALUE!` - Wrong data type in formula
- `#REF!` - Invalid cell reference

### Anomalies Detected
- **$0 budgets with spending** → Overspending or missing budget data
- **$0 costs on active projects** → Data entry incomplete or project not started
- **Extreme outliers** → Data entry errors or exceptional projects
- **Text in numeric fields** → "Error", "N/A", "TBD", "Pending"

### Missing Data Patterns
- Empty critical fields (Budget, GCA, SF area)
- Incomplete project records
- Missing division breakdowns
- Unavailable preliminary data

---

## Configuration

### Current Settings

**Model:** `gpt-4o` (advanced reasoning)  
**Query Type:** Auto-detected via keyword matching  
**Template:** `budget_calculation` (when calculation keywords found)  
**Priority:** Calculation keywords have highest priority  
**Template Style:** Dynamic placeholders (no hardcoded project names)

### Template Philosophy

**✅ CORRECT - Dynamic Template:**
```
[Project Name]: $[actual value from data]
```
AI uses actual project names from Data Context - scales to any portfolio size.

**❌ WRONG - Hardcoded Template:**
```
17175 Yonge St: $46,798,403
```
This would fail when new projects are added or names change.  

### Calculation Keywords

Triggers special calculation template:
```python
[
  "calculate", "add up", "sum", "total", "aggregate", "combine",
  "what is the total", "give me the total", "what's the sum",
  "across all projects", "for all projects"
]
```

### Budget Keywords

Secondary detection for budget-specific queries:
```python
["budget", "cost", "expense", "financial"]
```

---

## Technical Details

### Code Location

1. **Query Type Detection**
   - File: `src/production_mcp_integration.py`
   - Lines: 916-920
   - Function: Auto-detects query type from keywords

2. **Calculation Template**
   - File: `src/construction_prompts.py`
   - Lines: 127-196
   - Template: `"budget_calculation"`

3. **Keyword Matching**
   - File: `src/construction_prompts.py`
   - Lines: 710-729
   - Function: `get_query_type_from_keywords()`

### Response Structure

```json
{
  "success": true,
  "data": {
    "prompt_type": "budget_calculation",
    "ai_response": "⚠️ DATA QUALITY ALERT...",
    "ai_metadata": {
      "confidence_score": 0.90,
      "tokens_used": 1797,
      "cost_estimate": 0.07,
      "model_used": "gpt-4o"
    }
  }
}
```

---

## Testing

### Health Check
```bash
curl -s http://localhost:8000/health
```

### Calculation Test
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Add up total budget across all projects",
    "type": "enhanced_query",
    "parameters": {}
  }'
```

### Expected Response Indicators
- ✅ `"prompt_type": "budget_calculation"` - Template selected correctly
- ✅ `"Total Budget = $X + $Y + $Z = $[sum]"` - Calculation performed
- ⚠️ `"DATA QUALITY ALERT"` - Issues detected (if any)
- 📋 `"RECOMMENDATION:"` - Actionable guidance provided

---

## Troubleshooting

### AI Not Calculating

**Symptoms:** AI lists values but doesn't sum them

**Check:**
1. Query contains calculation keywords? ("add up", "sum", "total")
2. `prompt_type` in response is "budget_calculation"?
3. Server restarted after code changes?

**Fix:**
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
pkill -f "production_mcp_integration"
nohup ./start_web_server.sh > server_runtime.log 2>&1 &
```

### Wrong Template Selected

**Symptoms:** `prompt_type` is "general" or "budget_analysis" instead of "budget_calculation"

**Fix:** Add more explicit calculation keywords to query:
```
Instead of: "Show me project budgets"
Use: "Add up the total budget across all projects"
```

### Data Quality Not Reported

**Symptoms:** Calculation shown but no ⚠️ alerts for known errors

**Check:**
1. Spreadsheet errors visible in source data? (#DIV/0!, #ERROR!)
2. Data context includes full project records?
3. AI has access to detailed spreadsheet values?

**Enhancement:** Add explicit error markers to data extraction:
```python
# In data extraction code
if cell_value.startswith('#'):
    extracted_value = {"value": cell_value, "is_error": True}
```

---

## Real-World Example

### Actual Test (October 2, 2025)

**Query:**
```
"Add up the total budget across all projects and add up the total direct cost across all projects. Give me the two sums."
```

**AI Response:**
```
⚠️ DATA QUALITY ALERT - Calculation Attempted with Caveats

**Data Quality Issues Detected:**
- 72 Perth Avenue: Total Budget is $0, confirmed zero but unusual
- 6071 Azure Road: Total Direct Cost is $0, may need verification

**Calculation:**
Total Budget: $0 + $46,798,403 + $23,981,776 = $70,780,179
Total Direct Cost: $897,836 + $7,746,848 + $0 = $8,644,684

Remaining Budget: $70,780,179 - $8,644,684 = $62,135,495

**⚠️ RECOMMENDATION:**
1. Verify 72 Perth Avenue budget ($0 with $897K spent = overspending)
2. Confirm Azure Road direct cost accuracy ($0 may indicate project not started)

**ACTION ITEMS:**
- Review financial records for 72 Perth Avenue
- Ensure all costs accounted for in Azure Road project
- Consider revising budget allocations if necessary
```

**Result:**
- ✅ Both totals calculated correctly
- ⚠️ Two data quality issues identified
- 📋 Three specific recommendations provided
- 🎯 User has confidence in results with clear caveats

---

## Future Enhancements

### Planned (Test 6 - Division Cost Comparison)
- Cross-project division analysis
- Unit cost calculations ($/SF, $/GCA)
- Cost ratio comparisons (% of total budget)
- Ranking by efficiency metrics

### Under Consideration
- Historical trend detection (costs increasing/decreasing)
- Benchmark comparisons (vs industry standards)
- Predictive cost modeling (based on project phase)
- Automated data fix suggestions (formula corrections)

---

## Support

**Documentation:** See `docs/SESSION_SUCCESS_2025-10-02_DATA_QUALITY.md`  
**Roadmap:** See `docs/PARSER_IMPROVEMENTS_ROADMAP_V2.md`  
**Tests:** Run `pytest tests/proof_tester.py -v`  

**Server Logs:** `tail -f server_runtime.log`  
**Health Check:** `curl http://localhost:8000/health`  

---

**Last Updated:** October 2, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅

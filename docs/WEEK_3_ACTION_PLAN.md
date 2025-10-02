# Week 3 Action Plan (Oct 3-9, 2025)

**Goal:** Monitor production, implement Test 7, document query patterns  
**Status:** 🚀 **READY TO START**  
**Current:** v2.0.0 production ready, 100% test pass rate (6/6 tests)

---

## 📊 Week 3 Overview

```
Monday-Tuesday:     Production Monitoring & Feedback    ████░░░░ 0%
Wednesday-Thursday: Test 7 - Division Cost Comparison   ░░░░░░░░ 0%
Friday:             Query Pattern Documentation         ░░░░░░░░ 0%
────────────────────────────────────────────────────────────────
Overall Progress:                                       ░░░░░░░░ 0%
```

**Target:** 7/7 tests passing (117% coverage) + user documentation

---

## 📅 Day-by-Day Breakdown

### **Monday, Oct 3 - Production Monitoring (Day 1)** 📊

#### Morning: Server Health Check
**Tasks:**
- [ ] Check server logs for errors
  ```bash
  cd /home/egk/buildbridge-MCP/BuildBridge-MCP
  tail -f logs/server.log | grep -i error
  ```
- [ ] Verify all endpoints responding
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/api/projects
  ```
- [ ] Test Chat Interface V2 functionality
  - Load http://localhost:8000
  - Click 5+ project buttons
  - Try 3+ portfolio queries
  - Verify no UI errors

**Success Criteria:**
- ✅ Zero errors in logs (past 24 hours)
- ✅ All endpoints return 200 OK
- ✅ Chat V2 loads and responds correctly

#### Afternoon: Usage Metrics Collection
**Tasks:**
- [ ] Count total queries since launch (Oct 2, 4 PM)
  ```bash
  grep "Processing query" logs/server.log | wc -l
  ```
- [ ] Identify most common query patterns
  ```bash
  grep "Processing query" logs/server.log | tail -50 > queries.txt
  ```
- [ ] Track response times
  ```bash
  grep "Response time" logs/server.log | awk '{print $5}' | sort -n
  ```
- [ ] Note any errors or warnings

**Deliverable:** Create `docs/PRODUCTION_METRICS_OCT3.md` with findings

---

### **Tuesday, Oct 4 - User Feedback & Analysis (Day 2)** 📝

#### Morning: Feedback Collection
**Tasks:**
- [ ] Review query patterns from logs
- [ ] Categorize queries by type:
  - Single project queries (count, %)
  - Cross-project comparisons (count, %)
  - Portfolio calculations (count, %)
  - Division/cost-specific queries (count, %)
  - "What-if" or simulation queries (count, %)
  - Unclear/failed queries (count, %)

#### Afternoon: Priority Analysis
**Tasks:**
- [ ] Identify top 5 most requested query types
- [ ] Flag any queries that failed or gave poor responses
- [ ] Note feature requests or confusion points
- [ ] Determine if formula-awareness would help
  - Are users asking about calculated values?
  - Are there "what-if" questions?
  - Do users need formula explanations?

**Questions to Answer:**
1. Which Chat V2 buttons are most used?
2. Are portfolio queries working well?
3. Do users understand the interface?
4. Are there any data quality alerts triggered?
5. Should Test 7 focus on division costs or something else?

**Deliverable:** Create `docs/WEEK3_FEEDBACK_SUMMARY.md` with recommendations

---

### **Wednesday, Oct 5 - Test 7 Prep (Day 3)** 🎯

#### Morning: Ground Truth Extraction
**Location:** Work with project spreadsheets

**Tasks:**
1. [ ] **Open project spreadsheets** (via Google Sheets)
   - 72 Perth Avenue
   - 17175 Yonge St
   - Azure Road

2. [ ] **Extract Division 03 (Concrete) costs** for each project
   - Navigate to appropriate tab (Cost Breakdown, Division Summary, etc.)
   - Find "Division 03" or "Concrete" section
   - Record total cost for division

3. [ ] **Calculate unit costs** (Division Cost / Total GCA SF)
   ```
   72 Perth: $X / 214,384 SF = $Y.YY per SF
   17175 Yonge: $X / 269,141 SF = $Y.YY per SF
   Azure Road: $X / 376,332 SF = $Y.YY per SF
   ```

4. [ ] **Calculate ratios** (Division Cost / Total Budget)
   ```
   72 Perth: $X / $0 = N/A (or calculate vs direct cost)
   17175 Yonge: $X / $46,798,403 = Y.Y%
   Azure Road: $X / $23,981,776 = Y.Y%
   ```

5. [ ] **Update ground truth file**
   ```bash
   vim tests/ground_truth.json
   # Add section:
   "division_cost_comparison": {
     "query": "Compare Concrete Placing costs across all projects",
     "expected": {
       "72_perth": {
         "division_03_cost": <value>,
         "unit_cost_sf": <value>,
         "ratio_of_budget": <value>
       },
       # ... repeat for other projects
     }
   }
   ```

**Afternoon: Context Enhancement**
**Tasks:**
- [ ] Check if division costs are in formatted context
  ```bash
  # Test current context
  python -c "
  from src.parsers.google_sheet_manifest_parsers import get_formatted_data_for_ai
  context = get_formatted_data_for_ai('17175_yonge_st')
  print('Division' in context)
  "
  ```
- [ ] If not present, enhance `google_sheet_manifest_parsers.py`:
  - Add division cost breakdown to formatted output
  - Format: "Division 03 (Concrete): $X,XXX,XXX"
  - Include for all projects

**Deliverable:** Ground truth updated, division costs in AI context

---

### **Thursday, Oct 6 - Test 7 Implementation (Day 4)** 🔧

#### Morning: Test Implementation
**File:** `tests/proof_tester.py`

**Tasks:**
1. [ ] **Add test_division_comparison() method** (~150 lines)
   ```python
   def test_division_comparison(self, server_url: str) -> Dict:
       """Test 7: Division cost comparison across projects."""
       query = "Compare Concrete Placing costs across all projects, show table with project name, total cost, unit cost per SF, and percentage of total budget"
       
       # Send query
       response = self._send_query(server_url, query)
       
       # Extract values for each project
       projects = ['72_perth', '17175_yonge_st', 'azure_road']
       actual = {}
       
       for project in projects:
           # Extract division cost, unit cost, ratio
           cost = self._extract_division_cost(response, project)
           unit_cost = self._extract_unit_cost(response, project)
           ratio = self._extract_ratio(response, project)
           
           actual[project] = {
               'division_03_cost': cost,
               'unit_cost_sf': unit_cost,
               'ratio_of_budget': ratio
           }
       
       # Compare with ground truth
       expected = self.ground_truth['division_cost_comparison']['expected']
       
       return self._compare_results('Division Cost Comparison', expected, actual)
   ```

2. [ ] **Add extraction helper methods**
   - `_extract_division_cost()` - regex patterns for cost values
   - `_extract_unit_cost()` - patterns for "$/SF" values
   - `_extract_ratio()` - patterns for percentage values

3. [ ] **Update main test runner** to include Test 7
   ```python
   def run_all_tests(self):
       tests = [
           self.test_gca_totals,
           self.test_parking_stalls,
           self.test_total_direct_cost,
           self.test_project_locations,
           self.test_portfolio_totals,
           self.test_data_quality,
           self.test_division_comparison,  # NEW
       ]
   ```

#### Afternoon: Testing & Refinement
**Tasks:**
- [ ] Run Test 7
  ```bash
  cd /home/egk/buildbridge-MCP/BuildBridge-MCP
  pytest tests/proof_tester.py::test_division_comparison -v
  ```
- [ ] If fails, analyze AI response:
  - Is division data in context?
  - Does AI format response as table?
  - Are calculations shown?
  - Are all 3 projects included?

- [ ] Refine query wording if needed:
  - Try: "Compare Division 03 Concrete costs..."
  - Try: "Show comparison of Concrete Placing costs..."
  - Try: "Analyze Concrete costs across all projects..."

- [ ] Adjust extraction patterns if needed
- [ ] Run full test suite
  ```bash
  pytest tests/proof_tester.py -v
  ```

**Success Criteria:**
- ✅ Test 7 passes (all 3 projects, correct values)
- ✅ Full suite: 7/7 tests passing
- ✅ Pass rate: 117% coverage (vs 6/6 baseline)

**Deliverable:** Test 7 implemented and passing

---

### **Friday, Oct 7 - Query Documentation (Day 5)** 📚

#### Morning: Query Pattern Catalog
**File:** `docs/QUERY_PATTERNS.md` (NEW)

**Tasks:**
1. [ ] **Document query categories** with examples:
   
   **Simple Single-Project Queries:**
   ```
   "What is the total GCA for 17175 Yonge St?"
   "Show me the budget for Azure Road project"
   "How many parking stalls does 72 Perth have?"
   ```
   
   **Comparison Queries:**
   ```
   "Compare total budgets across all projects"
   "Which project has the highest GCA?"
   "Show parking stalls for each project"
   ```
   
   **Calculation Queries:**
   ```
   "Calculate total budget across all projects"
   "Add up total direct costs for all projects"
   "What is the sum of parking stalls?"
   ```
   
   **Division-Specific Queries:**
   ```
   "Compare Concrete Placing costs across all projects"
   "Show Division 03 costs per square foot for each project"
   "Which project has highest concrete costs?"
   ```
   
   **Ranking Queries:**
   ```
   "Rank projects by cost per square foot"
   "Which project has the best cost efficiency?"
   "Order projects by total budget, highest to lowest"
   ```

2. [ ] **Best Practices section:**
   - Be specific with names ("Concrete Placing" not "concrete")
   - Request format ("show table", "include unit costs")
   - Specify scope ("all projects" vs specific names)
   - Use proper project names (from sidebar buttons)

3. [ ] **Common Mistakes to Avoid:**
   - Typos in project names
   - Vague division names ("concrete" → "Division 03 Concrete Placing")
   - Unclear scope ("show costs" → "show costs for all projects")

#### Afternoon: Chat V2 Enhancements
**File:** `static/chat_interface_v2.html`

**Tasks:**
1. [ ] **Add tooltips to project buttons**
   ```javascript
   // Add title attributes with example queries
   button.title = "Click for project-specific queries like budget, GCA, costs";
   ```

2. [ ] **Add "Pro Tips" section to sidebar**
   ```html
   <div class="pro-tips" style="margin-top: 20px; padding: 15px; background: rgba(138, 43, 226, 0.1); border-radius: 8px;">
     <h4>💡 Pro Tips</h4>
     <ul style="font-size: 0.9em; line-height: 1.6;">
       <li>Be specific: "Division 03 Concrete" not "concrete"</li>
       <li>Request format: "show table" or "include unit costs"</li>
       <li>Specify scope: "all projects" or specific names</li>
       <li>Use sidebar buttons for quick queries</li>
     </ul>
   </div>
   ```

3. [ ] **Add example query hints**
   - On page load, show rotating example in placeholder
   - "Try: 'Compare total budgets across all projects'"
   - "Try: 'Calculate total GCA for all projects'"
   - "Try: 'Which project has highest cost per SF?'"

**Deliverable:** User-facing documentation and UI enhancements

---

## 📊 Week 3 Success Metrics

### Quantitative Targets:
- [ ] 7/7 tests passing (117% coverage)
- [ ] Zero production errors (past 7 days)
- [ ] Response time < 8 seconds (95th percentile)
- [ ] Query documentation complete (>500 words)

### Qualitative Targets:
- [ ] User feedback collected and analyzed
- [ ] Query patterns documented
- [ ] Division cost comparison working
- [ ] UI improvements implemented

---

## 🚨 Risk Management

### Potential Blockers:
1. **Ground truth data missing**
   - Mitigation: Request spreadsheet access early
   - Backup: Use estimates from visible data

2. **Test 7 extraction patterns fail**
   - Mitigation: Test multiple query variations
   - Backup: Refine patterns based on actual AI responses

3. **Division costs not in context**
   - Mitigation: Enhance parser to include division data
   - Backup: Request AI to calculate from raw data

### Rollback Plan:
If Test 7 blocks progress:
- Keep 6/6 tests as stable baseline
- Document Test 7 as "in progress"
- Move to Test 8 or query documentation

---

## 📝 Daily Standup Format

**Every morning, answer:**
1. What did I accomplish yesterday?
2. What am I working on today?
3. Any blockers or help needed?

**Track in:** `docs/WEEK3_DAILY_NOTES.md`

---

## 🎯 End-of-Week Deliverables

### Documentation:
- [ ] `docs/PRODUCTION_METRICS_OCT3.md` - Server health
- [ ] `docs/WEEK3_FEEDBACK_SUMMARY.md` - User insights
- [ ] `docs/QUERY_PATTERNS.md` - Query guide
- [ ] `docs/WEEK3_DAILY_NOTES.md` - Daily progress

### Code:
- [ ] `tests/ground_truth.json` - Updated with Test 7 data
- [ ] `tests/proof_tester.py` - Test 7 implementation
- [ ] `static/chat_interface_v2.html` - UI enhancements
- [ ] `src/parsers/google_sheet_manifest_parsers.py` - Division costs (if needed)

### Results:
- [ ] Test suite passing: 7/7 tests
- [ ] Test coverage: 117%
- [ ] Production stable: 0 critical errors
- [ ] Users documented: Query patterns guide

---

## 🎉 Week 3 Goal Statement

> **By Friday, Oct 7, we will have:**
> - ✅ Stable production (monitored and validated)
> - ✅ Test 7 passing (division cost comparison)
> - ✅ User documentation (query patterns guide)
> - ✅ 117% test coverage (7/7 tests)
> 
> **Setting us up for Week 4:**
> - Tests 8-9 (advanced analytics)
> - Enhanced UX features
> - Potential formula-awareness activation

---

## 📞 Resources & Help

### Key Files:
- Production server: `src/production_mcp_integration.py`
- Test framework: `tests/proof_tester.py`
- Ground truth: `tests/ground_truth.json`
- Parser: `src/parsers/google_sheet_manifest_parsers.py`
- Chat V2: `static/chat_interface_v2.html`

### Commands:
```bash
# Start server
./start_web_server.sh

# Run tests
pytest tests/proof_tester.py -v

# Check logs
tail -f logs/server.log

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"YOUR_QUERY_HERE"}'
```

### Documentation:
- Roadmap: `docs/PARSER_IMPROVEMENTS_ROADMAP_V2.md`
- Journey status: `docs/JOURNEY_STATUS_2025-10-02.md`
- Changelog: `CHANGELOG.md`

---

**Last Updated:** October 2, 2025 - 9:00 PM  
**Status:** 🚀 **READY TO BEGIN WEEK 3**  
**Next Action:** Monday morning - Production monitoring

Let's make it happen! 💪

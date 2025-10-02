# BuildBridge-MCP Proof Testing Suite

This directory contains comprehensive testing tools to validate the accuracy of BuildBridge-MCP queries against Google Sheets data.

## 📁 Files

- **`proof_tester.py`** - Automated Python test suite
- **`manual_curl_tests.sh`** - Manual CURL test script for interactive testing
- **`ground_truth.json`** - Ground truth data extracted from Google Sheets (generated)
- **`proof_test_results.json`** - Test results (generated after running tests)

## 🚀 Quick Start

### 1. Start the MCP Server
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
./start_buildbridge.sh
```

### 2. Generate Ground Truth Data
```bash
python scripts/create_ground_truth.py
```

This will create `tests/ground_truth.json` with current values from your Google Sheets.

### 3. Run Automated Tests
```bash
cd tests
python proof_tester.py
```

### 4. Run Manual CURL Tests (Optional)
```bash
cd tests
./manual_curl_tests.sh
```

## 📊 Test Categories

The test suite validates:

1. **Basic Project Information**
   - GCA (Gross Construction Area) totals
   - Parking stalls per project
   - Project locations

2. **Budget & Cost Analysis**
   - Total Direct Cost accuracy
   - Budget comparisons
   - Cost per square foot calculations

3. **Material-Specific Costs**
   - Concrete costs
   - Steel costs
   - Sitework costs

4. **Building Metrics**
   - Building areas (metric and imperial)
   - Functional units
   - Client information

5. **Aggregation & Statistics**
   - Portfolio totals
   - Average metrics
   - Comparative analysis

6. **Division-Specific Costs**
   - Below grade costs
   - CSI division breakdowns

7. **Timeline & Dates**
   - Budget dates
   - Last updated information

8. **Complex Multi-Criteria Queries**
   - Best value analysis
   - Resource intensity calculations

## 📈 Success Criteria

- **Exact Matches**: Project names, locations, clients (100%)
- **Numeric Values**: Within 1% tolerance for costs and areas
- **Integer Counts**: Exact match (parking stalls, units)
- **Overall Pass Rate**: > 95%

## 📝 Understanding Results

### Automated Test Output

```
🧪 Test 1: Total GCA Query
  ✅ PASSED

🧪 Test 2: Parking Stalls Query
  ❌ FAILED
    - 72 Perth Avenue: Expected 31 stalls, got 30 stalls

📊 Test Summary
Total Tests: 5
Passed: 4
Failed: 1
Success Rate: 80.0%
```

### Results JSON Structure

```json
{
  "timestamp": "2025-10-01T12:00:00",
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1,
    "success_rate": 80.0
  },
  "results": [
    {
      "test": "GCA Totals",
      "passed": true,
      "errors": [],
      "expected": {...},
      "actual": {...}
    }
  ]
}
```

## 🔧 Customization

### Test Different Server
```bash
python proof_tester.py --server http://localhost:8001
```

### Use Different Ground Truth
```bash
python proof_tester.py --ground-truth /path/to/custom_ground_truth.json
```

### Add Custom Tests

Edit `proof_tester.py` and add a new test method:

```python
def test_custom_query(self):
    """Test your custom query"""
    query = "Your custom question here"
    response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
    
    # Validation logic
    passed = True
    errors = []
    
    # Add your validation here
    
    self.results.append({
        "test": "Custom Query",
        "passed": passed,
        "errors": errors,
        "response": response.get('ai_response', '')
    })
```

Then add to `run_all_tests()`:
```python
self.test_custom_query()
```

## 🐛 Troubleshooting

### Ground Truth File Not Found
```
❌ Error: Ground truth file not found: tests/ground_truth.json
Run: python scripts/create_ground_truth.py
```

**Solution**: Generate ground truth data first.

### Cannot Connect to Server
```
❌ Cannot connect to server at http://localhost:8000
Make sure the server is running: ./start_buildbridge.sh
```

**Solution**: Start the MCP server.

### Test Failures Due to Data Updates
If Google Sheets data has been updated since ground truth generation:

```bash
# Regenerate ground truth
python scripts/create_ground_truth.py

# Re-run tests
python tests/proof_tester.py
```

### AI Service Not Available
Some tests require AI service. Check server health:

```bash
curl http://localhost:8000/health | jq '.ai_service_info'
```

Ensure `OPENAI_API_KEY` is set in your `.env` file.

## 📚 Related Documentation

- **[PROOF_TEST_PLAN.md](../docs/PROOF_TEST_PLAN.md)** - Comprehensive testing strategy
- **[AI_INTEGRATION_USAGE_GUIDE.md](../docs/AI_INTEGRATION_USAGE_GUIDE.md)** - AI service usage
- **[INTERACTION_GUIDE.md](../docs/INTERACTION_GUIDE.md)** - How to use the MCP server

## 🎯 Best Practices

1. **Regenerate Ground Truth Regularly**
   - Before major testing sessions
   - After Google Sheets updates
   - Weekly for active projects

2. **Run Tests Before Deployment**
   - Validate all tests pass
   - Check success rate > 95%
   - Review any failures

3. **Version Control Ground Truth**
   - Tag ground truth with dates
   - Keep historical snapshots
   - Track data evolution

4. **Monitor Test Performance**
   - Track response times
   - Monitor accuracy trends
   - Log failure patterns

## 🤝 Contributing

To add new test cases:

1. Identify the query pattern to test
2. Add expected values to ground truth
3. Implement test method in `proof_tester.py`
4. Add CURL command to `manual_curl_tests.sh`
5. Document in `PROOF_TEST_PLAN.md`

## 📄 License

Part of the BuildBridge-MCP project. See main LICENSE file.

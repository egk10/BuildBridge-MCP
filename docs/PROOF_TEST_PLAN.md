# BuildBridge-MCP Proof Test Plan 🏗️

**Comprehensive Testing Plan for Google Sheets Integration & Data Accuracy Validation**

---

## 📋 Executive Summary

This document outlines a comprehensive testing strategy to validate the BuildBridge-MCP system's ability to accurately query Google Sheets data and provide correct responses. The tests will use CURL commands to query the MCP server and compare results against local CSV exports from Google Sheets for accuracy verification.

### Test Objectives
1. ✅ Validate MCP server query processing accuracy
2. ✅ Verify Google Sheets data integration
3. ✅ Compare AI responses against ground truth data
4. ✅ Test multi-project data aggregation
5. ✅ Validate cost calculations and metrics
6. ✅ Ensure data consistency across different query types

---

## 🎯 Test Projects Configuration

Based on `.env` configuration:

| Project Name | Project ID | Google Sheet ID | Status |
|-------------|-----------|----------------|--------|
| Project P (Northside Residential) | `72_perth` | `1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k` | ✅ Active |
| Project Y | `17175_yonge_st` | `1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU` | ✅ Active |
| Project A | `azure_road` | `1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg` | ✅ Active |

---

## 📊 Phase 1: Ground Truth Data Preparation

### Step 1.1: Export Google Sheets to CSV

Create a script to export current Google Sheets data to CSV for validation:

```bash
#!/bin/bash
# export_ground_truth.sh

EXPORT_DIR="./tests/ground_truth_data"
mkdir -p "$EXPORT_DIR"

echo "📥 Exporting Google Sheets data to CSV..."

# Export each project's data
python3 -c "
import sys
sys.path.insert(0, 'src')
from connectors.google_sheets_connector import GoogleSheetsConnector
from secure_config import load_legacy_config
import json
import csv
from pathlib import Path

config = load_legacy_config()
connector = GoogleSheetsConnector(config)

projects = ['72_perth', '17175_yonge_st', 'azure_road']
export_dir = Path('$EXPORT_DIR')

for project_id in projects:
    print(f'Exporting {project_id}...')
    
    # Get normalized data from cache
    cache_file = Path('cache/normalized') / f'{project_id}.json'
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Export project summary
        output_file = export_dir / f'{project_id}_summary.csv'
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            project_data = data.get('project', {})
            for key, value in project_data.items():
                writer.writerow([key, value])
        
        print(f'  ✅ Exported to {output_file}')
    else:
        print(f'  ⚠️  Cache not found for {project_id}')
"

echo "✅ Export complete!"
```

### Step 1.2: Create Ground Truth JSON

Generate a structured ground truth file for automated comparison:

```python
# scripts/create_ground_truth.py
"""Create ground truth data from Google Sheets for testing validation"""

import json
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from connectors.google_sheets_connector import GoogleSheetsConnector
from secure_config import load_legacy_config

def extract_ground_truth():
    """Extract ground truth data from cached Google Sheets data"""
    
    config = load_legacy_config()
    projects = ['72_perth', '17175_yonge_st', 'azure_road']
    
    ground_truth = {
        "generated_at": datetime.now().isoformat(),
        "projects": {}
    }
    
    for project_id in projects:
        cache_file = Path(f'cache/normalized/{project_id}.json')
        
        if not cache_file.exists():
            print(f"⚠️  Cache not found for {project_id}")
            continue
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        project_data = data.get('project', {})
        
        ground_truth['projects'][project_id] = {
            'name': project_data.get('Project_Name'),
            'location': project_data.get('Location'),
            'total_budget': float(project_data.get('Total_Budget', 0)),
            'total_direct_cost': float(project_data.get('Total_Direct_Cost', 0)),
            'building_area_metric': float(project_data.get('Building_Area_Metric', 0)),
            'total_gca_sf': float(project_data.get('Total_GCA_SF', 0)),
            'parking_stalls': int(project_data.get('Parking_Stalls', 0)),
            'parking_below_grade': int(project_data.get('Parking_Below_Grade', 0)),
            'parking_total': int(project_data.get('Parking_Total', 0)),
        }
    
    # Save ground truth
    output_file = Path('tests/ground_truth.json')
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"✅ Ground truth saved to {output_file}")
    return ground_truth

if __name__ == "__main__":
    from datetime import datetime
    extract_ground_truth()
```

---

## 🧪 Phase 2: Test Query Definitions

### Category 1: Basic Project Information Queries

#### Test 1.1: Total GCA for All Projects
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total GCA (Gross Construction Area) for projects Project A, Project Y, and Project P (Northside Residential)?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project A: TBD SF
- Project Y: TBD SF
- Project P (Northside Residential): 205 SF
- **Total: Sum of above**

**Validation Criteria:**
- Response includes all three projects
- GCA values match ground truth ±1%
- Unit (SF or M²) is clearly stated

---

#### Test 1.2: Parking Stalls per Project
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many parking stalls does each project have: Project P (Northside Residential), Project Y, and Project A?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): 31 stalls (31 below grade)
- Project Y: TBD stalls
- Project A: TBD stalls

**Validation Criteria:**
- Each project's parking count is accurate
- Breakdown by above/below grade if available

---

#### Test 1.3: Project Locations
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the locations of the three projects: Project A, Project Y, and Project P?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general"
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): Toronto, ON
- Project Y: TBD
- Project A: TBD

---

### Category 2: Budget & Cost Analysis Queries

#### Test 2.1: Total Direct Cost for Each Project
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

**Expected Ground Truth:**
- Project P (Northside Residential): $897,836
- Project Y: TBD
- Project A: TBD

**Validation Criteria:**
- Currency formatted correctly
- Values match within $1000 tolerance
- All three projects included

---

#### Test 2.2: Budget Comparison
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare the Total Budget and Total Direct Cost for all three projects: Project A, Project Y, and Project P",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): Total Budget $0, Direct Cost $897,836
- Project Y: TBD
- Project A: TBD

---

#### Test 2.3: Cost per Square Foot Analysis
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the cost per square foot for each project based on Total Direct Cost and GCA",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Calculation:**
- Project P (Northside Residential): $897,836 / 205 SF = $4,379.20/SF
- Project Y: Calculate from data
- Project A: Calculate from data

---

### Category 3: Specific Material Cost Queries

#### Test 3.1: Concrete Costs for Project Y
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the unit cost and total cost of concrete for project Project Y?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true,
      "project_filter": "17175_yonge_st"
    }
  }' | jq '.'
```

**Data Required:**
- Check division costs for concrete (typically Division 3)
- Unit cost ($/CY or $/M³)
- Total cost
- Quantity

---

#### Test 3.2: Steel Costs Comparison
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare structural steel costs across all three projects",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

---

#### Test 3.3: Sitework Costs
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the sitework costs for each project?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): $0 (Subtotal_Siteworks)

---

### Category 4: Building Metrics & Specifications

#### Test 4.1: Building Area (Metric vs Imperial)
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the building area in both square feet and square meters for all projects",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): 17,427 M² and 205 SF (note: this seems inconsistent - validate)

---

#### Test 4.2: Functional Units
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many functional units (residential units, suites, etc.) does each project have?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general"
    }
  }' | jq '.'
```

---

#### Test 4.3: Client Information
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who are the clients for these three projects?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general"
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): ABC Development Corp

---

### Category 5: Aggregation & Statistical Queries

#### Test 5.1: Total Portfolio Value
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total combined budget and total direct cost across all three projects?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

**Expected Calculation:**
- Sum all Total_Budget values
- Sum all Total_Direct_Cost values

---

#### Test 5.2: Average Metrics
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the average cost per square foot, average parking stalls, and average building size across the three projects",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

---

#### Test 5.3: Largest/Smallest Comparisons
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which project has the largest GCA, most parking, and highest budget?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

---

### Category 6: Division-Specific Cost Queries

#### Test 6.1: Below Grade Costs
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the below grade construction costs for each project?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_data_context": true
    }
  }' | jq '.'
```

---

#### Test 6.2: Specific CSI Division Costs
```bash
# Test for each division
for division in "Division 3 - Concrete" "Division 5 - Metals" "Division 7 - Thermal and Moisture Protection" "Division 9 - Finishes"; do
  curl -X POST "http://localhost:8000/query" \
    -H "Content-Type: application/json" \
    -d "{
      \"query\": \"What are the costs for $division across all projects?\",
      \"type\": \"ai_query\",
      \"parameters\": {
        \"query_type\": \"budget_analysis\",
        \"include_data_context\": true
      }
    }" | jq '.'
  
  echo "---"
  sleep 2
done
```

---

### Category 7: Date and Timeline Queries

#### Test 7.1: Budget Dates
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "When was the budget last updated for each project?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general"
    }
  }' | jq '.'
```

**Expected Ground Truth:**
- Project P (Northside Residential): 14-Jun-24

---

### Category 8: Complex Multi-Criteria Queries

#### Test 8.1: Best Value Analysis
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which project offers the best value in terms of cost per square foot and which has the most efficient parking ratio (parking per unit area)?",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

---

#### Test 8.2: Resource Intensity
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the budget intensity (cost per square foot) and parking density (stalls per 1000 SF) for each project",
    "type": "ai_query",
    "parameters": {
      "query_type": "general",
      "include_data_context": true
    }
  }' | jq '.'
```

---

## 📝 Phase 3: Automated Test Script

Create a comprehensive test runner:

```python
#!/usr/bin/env python3
"""
Automated Proof Testing for BuildBridge-MCP
Validates query accuracy against ground truth data
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re

class BuildBridgeProofTester:
    """Automated tester for BuildBridge-MCP query accuracy"""
    
    def __init__(self, server_url="http://localhost:8000", ground_truth_file="tests/ground_truth.json"):
        self.server_url = server_url
        self.ground_truth = self.load_ground_truth(ground_truth_file)
        self.results = []
        
    def load_ground_truth(self, filepath: str) -> Dict:
        """Load ground truth data from JSON"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def query_mcp(self, query: str, query_type: str = "ai_query", **kwargs) -> Dict:
        """Send query to MCP server"""
        payload = {
            "query": query,
            "type": query_type,
            "parameters": kwargs
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/query",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def extract_number(self, text: str, pattern: str = None) -> float:
        """Extract numeric value from text response"""
        if pattern:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1).replace(',', ''))
        
        # Generic number extraction
        numbers = re.findall(r'\$?[\d,]+\.?\d*', text)
        if numbers:
            return float(numbers[0].replace('$', '').replace(',', ''))
        return None
    
    def test_gca_totals(self):
        """Test 1: Total GCA for all projects"""
        print("\n🧪 Test 1: Total GCA Query")
        
        query = "What is the total GCA (Gross Construction Area) for projects Project A, Project Y, and Project P (Northside Residential)?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        # Calculate expected total
        expected_total = sum(
            self.ground_truth['projects'][pid]['total_gca_sf']
            for pid in ['72_perth', '17175_yonge_st', 'azure_road']
        )
        
        # Extract from response
        response_text = response.get('ai_response', '')
        actual_values = {}
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            project_name = self.ground_truth['projects'][project_id]['name']
            # Try to extract GCA value near project name
            pattern = rf'{project_name}.*?(\d+[\d,]*\.?\d*)\s*SF'
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                actual_values[project_id] = float(match.group(1).replace(',', ''))
        
        # Validation
        passed = True
        errors = []
        
        for project_id, expected_gca in [(pid, self.ground_truth['projects'][pid]['total_gca_sf']) 
                                          for pid in ['72_perth', '17175_yonge_st', 'azure_road']]:
            actual_gca = actual_values.get(project_id)
            if actual_gca is None:
                passed = False
                errors.append(f"{project_id}: Value not found in response")
            elif abs(actual_gca - expected_gca) / max(expected_gca, 1) > 0.01:  # 1% tolerance
                passed = False
                errors.append(f"{project_id}: Expected {expected_gca}, got {actual_gca}")
        
        self.results.append({
            "test": "GCA Totals",
            "passed": passed,
            "errors": errors,
            "response": response_text[:200] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_parking_stalls(self):
        """Test 2: Parking stalls per project"""
        print("\n🧪 Test 2: Parking Stalls Query")
        
        query = "How many parking stalls does each project have: Project P (Northside Residential), Project Y, and Project A?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        response_text = response.get('ai_response', '')
        
        passed = True
        errors = []
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            expected_stalls = self.ground_truth['projects'][project_id]['parking_stalls']
            project_name = self.ground_truth['projects'][project_id]['name']
            
            # Extract parking value
            pattern = rf'{project_name}.*?(\d+)\s*(?:stalls?|parking)'
            match = re.search(pattern, response_text, re.IGNORECASE)
            
            if match:
                actual_stalls = int(match.group(1))
                if actual_stalls != expected_stalls:
                    passed = False
                    errors.append(f"{project_id}: Expected {expected_stalls}, got {actual_stalls}")
            else:
                passed = False
                errors.append(f"{project_id}: Parking stalls not found in response")
        
        self.results.append({
            "test": "Parking Stalls",
            "passed": passed,
            "errors": errors,
            "response": response_text[:200] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_direct_costs(self):
        """Test 3: Total Direct Cost accuracy"""
        print("\n🧪 Test 3: Total Direct Cost Query")
        
        query = "What is the Total Direct Cost for Project P (Northside Residential), Project Y, and Project A?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        response_text = response.get('ai_response', '')
        
        passed = True
        errors = []
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            expected_cost = self.ground_truth['projects'][project_id]['total_direct_cost']
            project_name = self.ground_truth['projects'][project_id]['name']
            
            # Extract cost value
            pattern = rf'{project_name}.*?\$\s*([\d,]+\.?\d*)'
            match = re.search(pattern, response_text, re.IGNORECASE)
            
            if match:
                actual_cost = float(match.group(1).replace(',', ''))
                tolerance = max(expected_cost * 0.01, 1000)  # 1% or $1000
                if abs(actual_cost - expected_cost) > tolerance:
                    passed = False
                    errors.append(f"{project_id}: Expected ${expected_cost:,.0f}, got ${actual_cost:,.0f}")
            else:
                passed = False
                errors.append(f"{project_id}: Cost not found in response")
        
        self.results.append({
            "test": "Total Direct Cost",
            "passed": passed,
            "errors": errors,
            "response": response_text[:200] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def run_all_tests(self):
        """Run all proof tests"""
        print("=" * 60)
        print("🏗️  BuildBridge-MCP Proof Testing Suite")
        print("=" * 60)
        print(f"Server: {self.server_url}")
        print(f"Ground Truth: {len(self.ground_truth['projects'])} projects")
        print("")
        
        # Health check first
        try:
            health = requests.get(f"{self.server_url}/health", timeout=5)
            if health.status_code == 200:
                print("✅ Server is healthy\n")
            else:
                print("⚠️  Server health check failed\n")
        except:
            print("❌ Cannot connect to server. Is it running?\n")
            return
        
        # Run tests
        self.test_gca_totals()
        self.test_parking_stalls()
        self.test_direct_costs()
        
        # Add more tests here...
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Save results
        results_file = Path('tests/proof_test_results.json')
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'server': self.server_url,
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': total_tests - passed_tests
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📝 Results saved to: {results_file}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = BuildBridgeProofTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
```

---

## 🚀 Phase 4: Execution Instructions

### Pre-requisites
1. Server must be running: `./start_buildbridge.sh`
2. Ground truth data must be generated: `python scripts/create_ground_truth.py`
3. All three Google Sheets must be accessible

### Running the Tests

```bash
# 1. Start the MCP server
./start_buildbridge.sh

# 2. In another terminal, generate ground truth
python scripts/create_ground_truth.py

# 3. Run automated proof tests
python tests/proof_tester.py

# 4. Or run manual CURL tests
bash tests/manual_curl_tests.sh

# 5. View results
cat tests/proof_test_results.json | jq '.'
```

---

## 📈 Phase 5: Success Criteria

### Accuracy Thresholds
- **Exact matches**: Project names, locations, clients (100%)
- **Numeric values**: Within 1% for costs and areas
- **Integer counts**: Exact match (parking stalls, units)
- **Calculations**: Within 2% for derived metrics

### Coverage Requirements
- ✅ All 3 projects queried successfully
- ✅ All 8 test categories executed
- ✅ At least 90% of individual tests pass
- ✅ No server errors or timeouts

### Performance Benchmarks
- Response time: < 5 seconds per query
- Accuracy: > 95% of values correct
- Completeness: All requested data points returned

---

## 📋 Phase 6: Results Documentation

### Test Results Template

```markdown
# BuildBridge-MCP Proof Test Results

**Test Date**: [Date]
**Tester**: [Name]
**Server Version**: [Version]

## Summary
- Total Tests: X
- Passed: X
- Failed: X
- Success Rate: X%

## Ground Truth Source
- Project P (Northside Residential): Google Sheet exported [date]
- Project Y: Google Sheet exported [date]
- Project A: Google Sheet exported [date]

## Detailed Results

### Test 1: Total GCA Query
- Status: ✅ PASSED / ❌ FAILED
- Expected: [values]
- Actual: [values]
- Variance: [%]
- Notes: [observations]

[Continue for each test...]

## Issues Found
1. [Issue description]
2. [Issue description]

## Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

## 🔄 Phase 7: Continuous Validation

### Regression Testing
- Run proof tests after each code change
- Automated CI/CD integration
- Weekly validation against live Google Sheets

### Data Drift Detection
- Compare current responses to baseline
- Alert on significant deviations
- Track accuracy trends over time

### Monitoring Script

```bash
#!/bin/bash
# continuous_validation.sh

while true; do
    echo "$(date): Running validation..."
    python tests/proof_tester.py
    
    if [ $? -eq 0 ]; then
        echo "✅ All tests passed"
    else
        echo "❌ Some tests failed - check logs"
        # Send alert
    fi
    
    sleep 3600  # Run hourly
done
```

---

## 📚 Appendix

### A. Ground Truth Data Structure
```json
{
  "generated_at": "2025-10-01T00:00:00",
  "projects": {
    "72_perth": {
      "name": "Project P (Northside Residential)",
      "location": "Toronto, ON",
      "total_budget": 0.0,
      "total_direct_cost": 897836.0,
      "building_area_metric": 17427.0,
      "total_gca_sf": 205.0,
      "parking_stalls": 31,
      "parking_below_grade": 31,
      "parking_total": 31
    }
  }
}
```

### B. API Endpoints Reference
- `POST /query` - Main query endpoint
- `GET /health` - Server health check
- `GET /logs` - View logs
- `WS /ws` - WebSocket connection

### C. Common Issues & Solutions
1. **Server not responding**: Check if process is running, verify port 8000
2. **Authentication errors**: Verify Google OAuth tokens are fresh
3. **Data mismatches**: Regenerate ground truth from latest Google Sheets
4. **Timeout errors**: Increase timeout, check network connectivity

---

## ✅ Completion Checklist

- [ ] Ground truth data exported from Google Sheets
- [ ] Ground truth JSON file created
- [ ] CSV exports validated
- [ ] All CURL test queries documented
- [ ] Automated test script created
- [ ] Server running and healthy
- [ ] All 8 test categories executed
- [ ] Results documented
- [ ] Accuracy threshold met (>95%)
- [ ] Performance benchmarks met
- [ ] Issues logged and tracked
- [ ] Recommendations documented

---

**Last Updated**: October 1, 2025  
**Version**: 1.0  
**Status**: Ready for Execution

#!/usr/bin/env python3
"""
Automated Proof Testing for BuildBridge-MCP
Validates query accuracy against ground truth data from Google Sheets
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import time

class BuildBridgeProofTester:
    """Automated tester for BuildBridge-MCP query accuracy"""
    
    def __init__(self, server_url="http://localhost:8000", ground_truth_file="tests/ground_truth.json"):
        self.server_url = server_url
        self.ground_truth_file = Path(ground_truth_file)
        self.ground_truth = self.load_ground_truth()
        self.results = []
        self.start_time = None
        
    def load_ground_truth(self) -> Dict:
        """Load ground truth data from JSON"""
        if not self.ground_truth_file.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: {self.ground_truth_file}\n"
                "Run: python scripts/create_ground_truth.py"
            )
        
        with open(self.ground_truth_file, 'r') as f:
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
        except requests.exceptions.Timeout:
            return {"error": "Request timeout after 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to server at {self.server_url}"}
        except Exception as e:
            return {"error": str(e)}
    
    def extract_number(self, text: str, pattern: str = None) -> Optional[float]:
        """Extract numeric value from text response"""
        if pattern:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        
        # Generic number extraction
        numbers = re.findall(r'\$?[\d,]+\.?\d*', text)
        if numbers:
            return float(numbers[0].replace('$', '').replace(',', ''))
        return None
    
    def calculate_variance(self, expected: float, actual: float) -> float:
        """Calculate percentage variance"""
        if expected == 0:
            return 0 if actual == 0 else 100
        return abs((actual - expected) / expected) * 100
    
    def test_gca_totals(self):
        """Test 1: Total GCA for all projects"""
        print("\n🧪 Test 1: Total GCA Query")
        
        query = "What is the total GCA (Gross Construction Area) for projects Azure Road, 17175 Yonge St, and 72 Perth Avenue?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        if "error" in response:
            self.results.append({
                "test": "GCA Totals",
                "passed": False,
                "errors": [f"Query failed: {response['error']}"],
                "response": ""
            })
            print(f"  ❌ FAILED: {response['error']}")
            return
        
        response_text = response.get('ai_response', str(response.get('data', '')))
        
        # Extract GCA values for each project
        actual_values = {}
        passed = True
        errors = []
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            project_info = self.ground_truth['projects'].get(project_id, {})
            project_name = project_info.get('name', project_id)
            expected_gca = project_info.get('total_gca_sf', 0)
            
            # Try multiple patterns to find GCA
            patterns = [
                rf'{project_name}.*?(\d+[\d,]*\.?\d*)\s*SF',
                rf'{project_name}.*?GCA.*?(\d+[\d,]*\.?\d*)',
                rf'{project_id}.*?(\d+[\d,]*\.?\d*)\s*SF'
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    actual_gca = float(match.group(1).replace(',', ''))
                    actual_values[project_id] = actual_gca
                    
                    variance = self.calculate_variance(expected_gca, actual_gca)
                    if variance > 1.0:  # 1% tolerance
                        passed = False
                        errors.append(
                            f"{project_name}: Expected {expected_gca:,.0f} SF, "
                            f"got {actual_gca:,.0f} SF (variance: {variance:.1f}%)"
                        )
                    found = True
                    break
            
            if not found:
                passed = False
                errors.append(f"{project_name}: GCA value not found in response")
        
        self.results.append({
            "test": "GCA Totals",
            "passed": passed,
            "errors": errors,
            "expected": {pid: self.ground_truth['projects'][pid]['total_gca_sf'] 
                        for pid in ['72_perth', '17175_yonge_st', 'azure_road']},
            "actual": actual_values,
            "response": response_text[:300] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_parking_stalls(self):
        """Test 2: Parking stalls per project"""
        print("\n🧪 Test 2: Parking Stalls Query")
        
        query = "How many parking stalls does each project have: 72 Perth Avenue, 17175 Yonge St, and Azure Road?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        if "error" in response:
            self.results.append({
                "test": "Parking Stalls",
                "passed": False,
                "errors": [f"Query failed: {response['error']}"],
                "response": ""
            })
            print(f"  ❌ FAILED: {response['error']}")
            return
        
        response_text = response.get('ai_response', str(response.get('data', '')))
        
        passed = True
        errors = []
        actual_values = {}
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            project_info = self.ground_truth['projects'].get(project_id, {})
            expected_stalls = project_info.get('parking_stalls', 0)
            project_name = project_info.get('name', project_id)
            
            # Extract parking value with multiple patterns
            patterns = [
                rf'{project_name}.*?(\d+)\s*(?:stalls?|parking)',
                rf'{project_name}.*?parking.*?(\d+)',
                rf'{project_id}.*?(\d+)\s*(?:stalls?|parking)'
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    actual_stalls = int(match.group(1))
                    actual_values[project_id] = actual_stalls
                    
                    if actual_stalls != expected_stalls:
                        passed = False
                        errors.append(
                            f"{project_name}: Expected {expected_stalls} stalls, "
                            f"got {actual_stalls} stalls"
                        )
                    found = True
                    break
            
            if not found:
                passed = False
                errors.append(f"{project_name}: Parking stalls not found in response")
        
        self.results.append({
            "test": "Parking Stalls",
            "passed": passed,
            "errors": errors,
            "expected": {pid: self.ground_truth['projects'][pid]['parking_stalls'] 
                        for pid in ['72_perth', '17175_yonge_st', 'azure_road']},
            "actual": actual_values,
            "response": response_text[:300] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_direct_costs(self):
        """Test 3: Total Direct Cost accuracy"""
        print("\n🧪 Test 3: Total Direct Cost Query")
        
        query = "What is the Total Direct Cost for 72 Perth Avenue, 17175 Yonge St, and Azure Road?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        if "error" in response:
            self.results.append({
                "test": "Total Direct Cost",
                "passed": False,
                "errors": [f"Query failed: {response['error']}"],
                "response": ""
            })
            print(f"  ❌ FAILED: {response['error']}")
            return
        
        response_text = response.get('ai_response', str(response.get('data', '')))
        
        passed = True
        errors = []
        actual_values = {}
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            project_info = self.ground_truth['projects'].get(project_id, {})
            expected_cost = project_info.get('total_direct_cost', 0)
            project_name = project_info.get('name', project_id)
            
            # Extract cost value
            patterns = [
                rf'{project_name}.*?\$\s*([\d,]+\.?\d*)',
                rf'{project_name}.*?cost.*?\$\s*([\d,]+\.?\d*)',
                rf'{project_id}.*?\$\s*([\d,]+\.?\d*)'
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    actual_cost = float(match.group(1).replace(',', ''))
                    actual_values[project_id] = actual_cost
                    
                    tolerance = max(expected_cost * 0.01, 1000)  # 1% or $1000
                    if abs(actual_cost - expected_cost) > tolerance:
                        passed = False
                        variance = self.calculate_variance(expected_cost, actual_cost)
                        errors.append(
                            f"{project_name}: Expected ${expected_cost:,.0f}, "
                            f"got ${actual_cost:,.0f} (variance: {variance:.1f}%)"
                        )
                    found = True
                    break
            
            if not found:
                passed = False
                errors.append(f"{project_name}: Cost not found in response")
        
        self.results.append({
            "test": "Total Direct Cost",
            "passed": passed,
            "errors": errors,
            "expected": {pid: self.ground_truth['projects'][pid]['total_direct_cost'] 
                        for pid in ['72_perth', '17175_yonge_st', 'azure_road']},
            "actual": actual_values,
            "response": response_text[:300] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_project_locations(self):
        """Test 4: Project locations"""
        print("\n🧪 Test 4: Project Locations Query")
        
        query = "What are the locations of the three projects: Azure Road, Yonge St, and Perth Avenue?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        if "error" in response:
            self.results.append({
                "test": "Project Locations",
                "passed": False,
                "errors": [f"Query failed: {response['error']}"],
                "response": ""
            })
            print(f"  ❌ FAILED: {response['error']}")
            return
        
        response_text = response.get('ai_response', str(response.get('data', '')))
        
        passed = True
        errors = []
        actual_values = {}
        
        for project_id in ['72_perth', '17175_yonge_st', 'azure_road']:
            project_info = self.ground_truth['projects'].get(project_id, {})
            expected_location = project_info.get('location', 'Unknown')
            project_name = project_info.get('name', project_id)
            
            # Check if location appears in response near project name
            if expected_location != 'Unknown' and expected_location in response_text:
                actual_values[project_id] = expected_location
            else:
                passed = False
                errors.append(f"{project_name}: Location '{expected_location}' not found in response")
        
        self.results.append({
            "test": "Project Locations",
            "passed": passed,
            "errors": errors,
            "expected": {pid: self.ground_truth['projects'][pid]['location'] 
                        for pid in ['72_perth', '17175_yonge_st', 'azure_road']},
            "actual": actual_values,
            "response": response_text[:300] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def test_portfolio_totals(self):
        """Test 5: Portfolio-wide totals"""
        print("\n🧪 Test 5: Portfolio Totals Query")
        
        query = "What is the total combined budget and total direct cost across all three projects?"
        response = self.query_mcp(query, query_type="ai_query", include_data_context=True)
        
        if "error" in response:
            self.results.append({
                "test": "Portfolio Totals",
                "passed": False,
                "errors": [f"Query failed: {response['error']}"],
                "response": ""
            })
            print(f"  ❌ FAILED: {response['error']}")
            return
        
        response_text = response.get('ai_response', str(response.get('data', '')))
        
        expected_totals = self.ground_truth.get('portfolio_totals', {})
        expected_budget = expected_totals.get('total_budget', 0)
        expected_direct = expected_totals.get('total_direct_cost', 0)
        
        errors = []
        passed = True
        
        # Try to find total budget and direct cost in response
        budget_match = re.search(r'total.*?budget.*?\$\s*([\d,]+\.?\d*)', response_text, re.IGNORECASE)
        direct_match = re.search(r'total.*?direct.*?cost.*?\$\s*([\d,]+\.?\d*)', response_text, re.IGNORECASE)
        
        if budget_match:
            actual_budget = float(budget_match.group(1).replace(',', ''))
            variance = self.calculate_variance(expected_budget, actual_budget)
            if variance > 1.0:
                passed = False
                errors.append(f"Total Budget: Expected ${expected_budget:,.0f}, got ${actual_budget:,.0f} (variance: {variance:.1f}%)")
        else:
            errors.append("Total Budget not found in response")
        
        if direct_match:
            actual_direct = float(direct_match.group(1).replace(',', ''))
            variance = self.calculate_variance(expected_direct, actual_direct)
            if variance > 1.0:
                passed = False
                errors.append(f"Total Direct Cost: Expected ${expected_direct:,.0f}, got ${actual_direct:,.0f} (variance: {variance:.1f}%)")
        else:
            errors.append("Total Direct Cost not found in response")
        
        self.results.append({
            "test": "Portfolio Totals",
            "passed": passed,
            "errors": errors,
            "expected": expected_totals,
            "response": response_text[:300] + "..."
        })
        
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")
        if errors:
            for error in errors:
                print(f"    - {error}")
    
    def run_all_tests(self):
        """Run all proof tests"""
        self.start_time = time.time()
        
        print("=" * 60)
        print("🏗️  BuildBridge-MCP Proof Testing Suite")
        print("=" * 60)
        print(f"Server: {self.server_url}")
        print(f"Ground Truth: {self.ground_truth_file}")
        print(f"Projects: {len(self.ground_truth['projects'])}")
        print("")
        
        # Health check first
        try:
            health = requests.get(f"{self.server_url}/health", timeout=5)
            if health.status_code == 200:
                health_data = health.json()
                print(f"✅ Server is healthy")
                if 'ai_service_info' in health_data:
                    ai_info = health_data['ai_service_info']
                    print(f"   AI Service: {'Enabled' if ai_info.get('enabled') else 'Disabled'}")
                    if ai_info.get('enabled'):
                        print(f"   Model: {ai_info.get('model', 'Unknown')}")
                print()
            else:
                print("⚠️  Server health check returned non-200 status\n")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure the server is running: ./start_buildbridge.sh\n")
            return False
        
        # Run tests
        self.test_gca_totals()
        time.sleep(1)  # Rate limiting
        
        self.test_parking_stalls()
        time.sleep(1)
        
        self.test_direct_costs()
        time.sleep(1)
        
        self.test_project_locations()
        time.sleep(1)
        
        self.test_portfolio_totals()
        
        # Summary
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"Total Time: {total_time:.1f}s")
        
        # Save results
        results_dir = Path(__file__).parent
        results_file = results_dir / 'proof_test_results.json'
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'server': self.server_url,
                'ground_truth_source': str(self.ground_truth_file),
                'ground_truth_generated': self.ground_truth.get('generated_at'),
                'total_time_seconds': total_time,
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': total_tests - passed_tests,
                    'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📝 Detailed results saved to: {results_file}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Query accuracy validated successfully.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Review the details above.")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BuildBridge-MCP Proof Tester')
    parser.add_argument('--server', default='http://localhost:8000', help='MCP server URL')
    parser.add_argument('--ground-truth', default='tests/ground_truth.json', help='Ground truth file path')
    
    args = parser.parse_args()
    
    try:
        tester = BuildBridgeProofTester(server_url=args.server, ground_truth_file=args.ground_truth)
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

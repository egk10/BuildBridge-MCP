#!/bin/bash
# Manual CURL Test Suite for BuildBridge-MCP
# Run individual queries to test MCP server responses

SERVER_URL="${SERVER_URL:-http://localhost:8000}"
SLEEP_TIME=2

echo "======================================================================"
echo "🏗️  BuildBridge-MCP Manual CURL Test Suite"
echo "======================================================================"
echo "Server: $SERVER_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a test
run_test() {
    local test_num=$1
    local test_name=$2
    local query=$3
    local query_type=${4:-ai_query}
    
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🧪 Test $test_num: $test_name${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Query: $query"
    echo ""
    
    curl -X POST "$SERVER_URL/query" \
      -H "Content-Type: application/json" \
      -d "{
        \"query\": \"$query\",
        \"type\": \"$query_type\",
        \"parameters\": {
          \"query_type\": \"general\",
          \"include_data_context\": true
        }
      }" \
      -s | jq '.'
    
    sleep $SLEEP_TIME
}

# Check server health first
echo "Checking server health..."
curl -s "$SERVER_URL/health" | jq '.' || {
    echo "❌ Error: Cannot connect to server at $SERVER_URL"
    echo "   Make sure the server is running: ./start_buildbridge.sh"
    exit 1
}

echo ""
read -p "Press Enter to start tests..."

# ====================================================================
# Category 1: Basic Project Information
# ====================================================================

run_test "1.1" "Total GCA for All Projects" \
    "What is the total GCA (Gross Construction Area) for projects Azure Road, 17175 Yonge St, and 72 Perth Avenue?"

run_test "1.2" "Parking Stalls per Project" \
    "How many parking stalls does each project have: 72 Perth Avenue, 17175 Yonge St, and Azure Road?"

run_test "1.3" "Project Locations" \
    "What are the locations of the three projects: Azure Road, Yonge St, and Perth Avenue?"

# ====================================================================
# Category 2: Budget & Cost Analysis
# ====================================================================

run_test "2.1" "Total Direct Cost" \
    "What is the Total Direct Cost for 72 Perth Avenue, 17175 Yonge St, and Azure Road?"

run_test "2.2" "Budget Comparison" \
    "Compare the Total Budget and Total Direct Cost for all three projects: Azure, Yonge, and Perth"

run_test "2.3" "Cost per Square Foot" \
    "Calculate the cost per square foot for each project based on Total Direct Cost and GCA"

# ====================================================================
# Category 3: Material-Specific Costs
# ====================================================================

run_test "3.1" "Concrete Costs for Yonge St" \
    "What is the unit cost and total cost of concrete for project 17175 Yonge St?"

run_test "3.2" "Steel Costs Comparison" \
    "Compare structural steel costs across all three projects"

run_test "3.3" "Sitework Costs" \
    "What are the sitework costs for each project?"

# ====================================================================
# Category 4: Building Metrics
# ====================================================================

run_test "4.1" "Building Area (Metric vs Imperial)" \
    "Show me the building area in both square feet and square meters for all projects"

run_test "4.2" "Functional Units" \
    "How many functional units (residential units, suites, etc.) does each project have?"

run_test "4.3" "Client Information" \
    "Who are the clients for these three projects?"

# ====================================================================
# Category 5: Aggregation & Statistics
# ====================================================================

run_test "5.1" "Total Portfolio Value" \
    "What is the total combined budget and total direct cost across all three projects?"

run_test "5.2" "Average Metrics" \
    "Calculate the average cost per square foot, average parking stalls, and average building size across the three projects"

run_test "5.3" "Largest/Smallest Comparisons" \
    "Which project has the largest GCA, most parking, and highest budget?"

# ====================================================================
# Category 6: Division-Specific Costs
# ====================================================================

run_test "6.1" "Below Grade Costs" \
    "What are the below grade construction costs for each project?"

run_test "6.2" "Division 3 - Concrete" \
    "What are the costs for Division 3 - Concrete across all projects?"

# ====================================================================
# Category 7: Timeline & Dates
# ====================================================================

run_test "7.1" "Budget Dates" \
    "When was the budget last updated for each project?"

# ====================================================================
# Category 8: Complex Queries
# ====================================================================

run_test "8.1" "Best Value Analysis" \
    "Which project offers the best value in terms of cost per square foot and which has the most efficient parking ratio?"

run_test "8.2" "Resource Intensity" \
    "Calculate the budget intensity (cost per square foot) and parking density (stalls per 1000 SF) for each project"

# ====================================================================
# Summary
# ====================================================================

echo ""
echo "======================================================================"
echo "✅ All manual tests complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Review the responses above"
echo "2. Compare with ground truth data in tests/ground_truth.json"
echo "3. Run automated validation: python tests/proof_tester.py"
echo ""

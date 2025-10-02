#!/bin/bash
# Complete Proof Testing Workflow
# Runs all steps needed to validate BuildBridge-MCP accuracy

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================"
echo "🏗️  BuildBridge-MCP Complete Proof Testing Workflow"
echo -e "======================================================================${NC}"
echo ""

# Step 1: Check if server is running
echo -e "${YELLOW}📡 Step 1: Checking server status...${NC}"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Web server is running${NC}"
else
    echo -e "${RED}❌ Web server is not running${NC}"
    echo ""
    echo "For proof testing, you need the WEB SERVER (not MCP server):"
    echo "  ./start_web_server.sh"
    echo ""
    echo "Note: './start_buildbridge.sh' starts the MCP server (for VS Code/Claude)"
    echo "      but proof tests need the web server for HTTP/CURL access."
    echo ""
    exit 1
fi
echo ""

# Step 2: Check if cache exists
echo -e "${YELLOW}💾 Step 2: Checking Google Sheets cache...${NC}"
if [ -f "cache/normalized/72_perth.json" ] && \
   [ -f "cache/normalized/17175_yonge_st.json" ] && \
   [ -f "cache/normalized/azure_road.json" ]; then
    echo -e "${GREEN}✅ Cache files found${NC}"
    
    # Show cache age
    CACHE_AGE=$(find cache/normalized -name "*.json" -type f -printf '%T@\n' | sort -n | tail -1)
    CACHE_DATE=$(date -d @"$CACHE_AGE" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "unknown")
    echo "   Last updated: $CACHE_DATE"
else
    echo -e "${RED}❌ Cache files not found${NC}"
    echo ""
    echo "Please refresh the cache first:"
    echo "  python scripts/refresh_manifest_local.py"
    echo ""
    exit 1
fi
echo ""

# Step 3: Generate ground truth
echo -e "${YELLOW}🎯 Step 3: Generating ground truth from Google Sheets...${NC}"
python scripts/create_ground_truth.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Ground truth generated successfully${NC}"
else
    echo -e "${RED}❌ Ground truth generation failed${NC}"
    exit 1
fi
echo ""

# Step 4: Show ground truth summary
if [ -f "tests/ground_truth.json" ]; then
    echo -e "${YELLOW}📊 Ground Truth Summary:${NC}"
    python -c "
import json
with open('tests/ground_truth.json', 'r') as f:
    data = json.load(f)
    print(f\"  Projects: {len(data['projects'])}\")
    print(f\"  Total Budget: \${data['portfolio_totals']['total_budget']:,.0f}\")
    print(f\"  Total Direct Cost: \${data['portfolio_totals']['total_direct_cost']:,.0f}\")
    print(f\"  Total GCA: {data['portfolio_totals']['total_gca_sf']:,.0f} SF\")
    print(f\"  Total Parking: {data['portfolio_totals']['total_parking']:,} stalls\")
" || echo "  (Could not parse ground truth)"
    echo ""
fi

# Ask user to confirm
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
read -p "Ready to run automated tests? (y/n) " -n 1 -r
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 0
fi

# Step 5: Run automated tests
echo -e "${YELLOW}🧪 Step 4: Running automated proof tests...${NC}"
echo ""
python tests/proof_tester.py
TEST_RESULT=$?
echo ""

# Step 6: Show results
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}======================================================================"
    echo "🎉 SUCCESS: All tests passed!"
    echo -e "======================================================================${NC}"
else
    echo -e "${RED}======================================================================"
    echo "⚠️  WARNING: Some tests failed"
    echo -e "======================================================================${NC}"
fi
echo ""

# Step 7: Show results file
if [ -f "tests/proof_test_results.json" ]; then
    echo -e "${YELLOW}📝 Detailed results saved to:${NC}"
    echo "   tests/proof_test_results.json"
    echo ""
    
    echo -e "${YELLOW}View results:${NC}"
    echo "   cat tests/proof_test_results.json | jq '.summary'"
    echo ""
    
    # Show summary
    echo -e "${YELLOW}Summary:${NC}"
    python -c "
import json
with open('tests/proof_test_results.json', 'r') as f:
    data = json.load(f)
    summary = data['summary']
    print(f\"  Total Tests: {summary['total']}\")
    print(f\"  Passed: {summary['passed']}\")
    print(f\"  Failed: {summary['failed']}\")
    print(f\"  Success Rate: {summary['success_rate']:.1f}%\")
    print(f\"  Total Time: {data['total_time_seconds']:.1f}s\")
" 2>/dev/null || echo "  (Could not parse results)"
    echo ""
fi

# Step 8: Optional manual tests
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
read -p "Run manual CURL tests for interactive exploration? (y/n) " -n 1 -r
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./tests/manual_curl_tests.sh
fi

echo ""
echo -e "${GREEN}======================================================================"
echo "✅ Proof testing workflow complete!"
echo -e "======================================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review test results in tests/proof_test_results.json"
echo "  2. Compare responses with ground truth data"
echo "  3. Document any issues or improvements needed"
echo "  4. Run tests again after making changes"
echo ""

exit $TEST_RESULT

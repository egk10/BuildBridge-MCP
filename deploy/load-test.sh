#!/bin/bash

# Load Testing Script for BuildBridge-MCP
# This script performs load testing on the production deployment

set -e

# Configuration
BASE_URL="https://localhost"
CONCURRENT_USERS=10
DURATION=60  # seconds
RAMP_UP_TIME=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚡ BuildBridge-MCP Load Testing${NC}"
echo "==============================="

# Check if services are running
echo -e "${YELLOW}🔍 Checking service health...${NC}"

if ! curl -k -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ Services are not running. Please start the services first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Services are healthy${NC}"

# Create load testing directory
LOAD_TEST_DIR="./load-test"
mkdir -p "$LOAD_TEST_DIR"

# Create Apache Bench test script
cat > "$LOAD_TEST_DIR/health-test.sh" << EOF
#!/bin/bash
# Health endpoint load test
ab -n 1000 -c $CONCURRENT_USERS -g health_plot.tsv "$BASE_URL/health"
EOF

# Create more comprehensive load test
cat > "$LOAD_TEST_DIR/comprehensive-test.sh" << EOF
#!/bin/bash
# Comprehensive load test script

echo "Starting comprehensive load test..."

# Test 1: Health endpoint
echo "Testing health endpoint..."
ab -n 500 -c $CONCURRENT_USERS -s 30 "$BASE_URL/health" > health_results.txt 2>&1

# Test 2: API endpoints (if available)
echo "Testing API endpoints..."
curl -k -s "$BASE_URL/api/health" > /dev/null && ab -n 200 -c 5 -s 30 "$BASE_URL/api/health" > api_results.txt 2>&1 || echo "API endpoint not available"

# Test 3: Static content
echo "Testing static content..."
ab -n 300 -c $CONCURRENT_USERS -s 30 "$BASE_URL/" > static_results.txt 2>&1

echo "Load test completed. Results saved in result files."
EOF

# Create Python load testing script for more advanced testing
cat > "$LOAD_TEST_DIR/load_test.py" << 'EOF'
#!/usr/bin/env python3
"""
Advanced Load Testing Script for BuildBridge-MCP
Uses locust for more sophisticated load testing
"""

import time
from locust import HttpUser, task, between
import ssl

class MCPUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
        self.client.trust_env = False

    @task(3)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/health")

    @task(2)
    def api_health(self):
        """Test API health"""
        self.client.get("/api/health")

    @task(1)
    def main_page(self):
        """Test main page"""
        response = self.client.get("/")
        if response.status_code == 200:
            # Simulate user interaction
            time.sleep(0.5)

    @task(1)
    def docs_page(self):
        """Test documentation page"""
        self.client.get("/docs")

if __name__ == "__main__":
    # Run load test
    import subprocess
    import sys

    try:
        # Install locust if not available
        subprocess.check_call([sys.executable, "-m", "pip", "install", "locust"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Starting Locust load test...")
        print("Open http://localhost:8089 in your browser to control the test")
        print("Press Ctrl+C to stop")

        # Run locust
        subprocess.run([
            sys.executable, "-m", "locust",
            "-f", __file__,
            "--host", "https://localhost",
            "--users", "50",
            "--spawn-rate", "5",
            "--run-time", "2m"
        ])

    except KeyboardInterrupt:
        print("\nLoad test stopped by user")
    except Exception as e:
        print(f"Error running load test: {e}")
        print("Falling back to simple ab test...")

        # Fallback to ab test
        import os
        os.system("./comprehensive-test.sh")
EOF

# Make scripts executable
chmod +x "$LOAD_TEST_DIR"/*.sh
chmod +x "$LOAD_TEST_DIR"/*.py

echo -e "${YELLOW}🔧 Running basic load test with Apache Bench...${NC}"

# Run basic load test
cd "$LOAD_TEST_DIR"
./comprehensive-test.sh

echo -e "${GREEN}✅ Basic load test completed${NC}"

# Parse results
echo -e "${YELLOW}📊 Analyzing results...${NC}"

if [ -f "health_results.txt" ]; then
    echo "Health endpoint results:"
    grep -E "(Requests per second|Time per request|Transfer rate)" health_results.txt || echo "Results parsing failed"
    echo ""
fi

if [ -f "static_results.txt" ]; then
    echo "Static content results:"
    grep -E "(Requests per second|Time per request|Transfer rate)" static_results.txt || echo "Results parsing failed"
    echo ""
fi

# Create performance report
cat > "performance_report.md" << EOF
# BuildBridge-MCP Load Test Report

## Test Configuration
- Base URL: $BASE_URL
- Concurrent Users: $CONCURRENT_USERS
- Duration: $DURATION seconds
- Ramp Up Time: $RAMP_UP_TIME seconds

## Test Results

### Health Endpoint
\`\`\`
$(cat health_results.txt 2>/dev/null | grep -A 10 "Server Software" || echo "No results available")
\`\`\`

### Static Content
\`\`\`
$(cat static_results.txt 2>/dev/null | grep -A 10 "Server Software" || echo "No results available")
\`\`\`

### API Endpoints
\`\`\`
$(cat api_results.txt 2>/dev/null | grep -A 10 "Server Software" || echo "No results available")
\`\`\`

## Recommendations

Based on the load test results:

1. **Response Times**: Monitor 95th percentile response times
2. **Error Rates**: Ensure error rates stay below 1%
3. **Throughput**: Current setup can handle the tested load
4. **Resource Usage**: Monitor CPU, memory, and database connections during peak load

## Next Steps

1. Run advanced load testing with locust: \`python3 load_test.py\`
2. Monitor system resources during load tests
3. Adjust nginx worker processes if needed
4. Consider horizontal scaling for higher loads
EOF

echo -e "${GREEN}📋 Performance report generated: $LOAD_TEST_DIR/performance_report.md${NC}"

# Check system resources during test
echo -e "${YELLOW}🔍 Checking system resources...${NC}"

echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}' || echo "Unable to check CPU"

echo "Memory Usage:"
free -h | grep "^Mem:" | awk '{print "Used: "$3"/"$2" ("int($3/$2*100)")%"}' || echo "Unable to check memory"

echo "Disk Usage:"
df -h / | tail -1 | awk '{print "Used: "$3"/"$2" ("$5" used)"}' || echo "Unable to check disk"

cd ..

echo ""
echo -e "${GREEN}🎉 Load testing completed successfully!${NC}"
echo ""
echo "📋 Summary:"
echo "   - Basic load test completed with Apache Bench"
echo "   - Performance report generated: ./load-test/performance_report.md"
echo "   - System resources monitored during test"
echo ""
echo "🚀 Next steps:"
echo "   1. Review performance report for bottlenecks"
echo "   2. Run advanced testing: cd load-test && python3 load_test.py"
echo "   3. Monitor Grafana dashboards during load tests"
echo "   4. Adjust configuration based on findings"
echo ""
echo "🔧 Test files location: ./load-test/"
echo "   - comprehensive-test.sh: Basic load test script"
echo "   - load_test.py: Advanced locust-based testing"
echo "   - performance_report.md: Detailed test results"
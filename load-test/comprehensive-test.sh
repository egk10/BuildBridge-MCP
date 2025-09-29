#!/bin/bash
# Comprehensive load test script

echo "Starting comprehensive load test..."

# Test 1: Health endpoint
echo "Testing health endpoint..."
ab -n 500 -c 10 -s 30 "https://localhost/health" > health_results.txt 2>&1

# Test 2: API endpoints (if available)
echo "Testing API endpoints..."
curl -k -s "https://localhost/api/health" > /dev/null && ab -n 200 -c 5 -s 30 "https://localhost/api/health" > api_results.txt 2>&1 || echo "API endpoint not available"

# Test 3: Static content
echo "Testing static content..."
ab -n 300 -c 10 -s 30 "https://localhost/" > static_results.txt 2>&1

echo "Load test completed. Results saved in result files."

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

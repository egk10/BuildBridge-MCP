#!/usr/bin/env bash
set -euo pipefail

# Start the Construction Management MCP Server
# This script sets up the Python path and runs the MCP server

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [[ ! -d .venv ]]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Set Python path to include src directory
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

echo "🚀 Starting Construction Management MCP Server..."
echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo ""
echo "Available tools:"
echo "- search_projects: Search for projects by natural language"
echo "- get_project_status: Get detailed project status"
echo "- analyze_budget: Analyze budget performance"
echo "- get_schedule_updates: Get schedule milestones and delays"
echo "- search_documents: Search construction documents"
echo "- generate_report: Generate various reports"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Check for test mode argument
if [[ "${1:-}" == "--test" ]]; then
    echo "🧪 Running MCP server initialization test..."
    START_TIME=$(date +%s.%3N)
    exec python3.12 src/main.py --test
fi

# Run the MCP server
exec python3.12 src/main.py

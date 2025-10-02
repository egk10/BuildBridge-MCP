#!/bin/bash
# Start BuildBridge-MCP in Web Server Mode for CURL Testing
# This script starts the FastAPI web server for HTTP/REST testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for virtual environment
VENV_FOUND=""
if [[ -d buildbridge_venv ]]; then
    VENV_FOUND="buildbridge_venv"
elif [[ -d .venv ]]; then
    VENV_FOUND=".venv"
elif [[ -d venv ]]; then
    VENV_FOUND="venv"
fi

if [[ -z "$VENV_FOUND" ]]; then
    echo "❌ No virtual environment found."
    exit 1
fi

echo "✅ Found virtual environment: $VENV_FOUND"

# Activate virtual environment
source "$VENV_FOUND/bin/activate"

# Set Python path
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

# Server settings
HOST="${SERVER_HOST:-localhost}"
PORT="${SERVER_PORT:-8000}"

echo ""
echo "======================================================================"
echo "🌐 Starting BuildBridge-MCP Web Server (for CURL testing)"
echo "======================================================================"
echo "Server: http://$HOST:$PORT"
echo "API Docs: http://$HOST:$PORT/docs"
echo "Health Check: http://$HOST:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"
echo ""

# Start the web server
exec python src/production_mcp_integration.py --mode server --host "$HOST" --port "$PORT"

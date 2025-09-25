#!/usr/bin/env bash
set -euo pipefail

# Start the BuildBridge Web Chat Server
# This script activates the virtual environment and starts the FastAPI web server

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists (try multiple common names)
VENV_FOUND=""
VENV_PATH=""

if [[ -d buildbridge_venv ]]; then
    VENV_FOUND="buildbridge_venv"
    VENV_PATH="buildbridge_venv"
elif [[ -d .venv ]]; then
    VENV_FOUND=".venv"
    VENV_PATH=".venv"
elif [[ -d venv ]]; then
    VENV_FOUND="venv"
    VENV_PATH="venv"
fi

if [[ -z "$VENV_FOUND" ]]; then
    echo "❌ No virtual environment found. Please create one first." >&2
    echo "💡 Try: python -m venv buildbridge_venv" >&2
    echo "Then: source buildbridge_venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi

echo "✅ Found virtual environment: $VENV_FOUND" >&2

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set Python path to include src directory
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

echo "🌐 Starting BuildBridge Web Chat Server..." >&2
echo "📁 Working directory: $(pwd)" >&2
echo "🐍 Python executable: $(which python)" >&2
echo "📚 Python path: $PYTHONPATH" >&2
echo "" >&2
echo "🚀 Web Server Features:" >&2
echo "- 💬 Chat Interface: http://localhost:8000/chat_interface.html" >&2
echo "- 📡 API Endpoint: http://localhost:8000/chat" >&2
echo "- 📊 Google Sheets Integration: Live project data" >&2
echo "- 🤖 AI Query Processing: Natural language construction queries" >&2
echo "- 📈 Project Analytics: Budget, schedule, and status reporting" >&2
echo "" >&2
echo "📝 Example queries you can ask:" >&2
echo "  'How many units are in the Yonge Street project?'" >&2
echo "  'Show me all projects over budget'" >&2
echo "  'What is the status of Azure Road project?'" >&2
echo "" >&2
echo "Press Ctrl+C to stop the server" >&2
echo "" >&2

# Run the web server in server mode
exec python src/production_mcp_integration.py --mode server
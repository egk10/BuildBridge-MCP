#!/usr/bin/env bash
set -euo pipefail

# Start the BuildBridge-MCP Server with proper venv
# This script activates the buildbridge_venv and runs the MCP server

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
    echo "💡 Try one of these commands:" >&2
    echo "   python -m venv buildbridge_venv" >&2
    echo "   python -m venv .venv" >&2
    echo "   python -m venv venv" >&2
    echo "" >&2
    echo "Then activate and install dependencies:" >&2
    echo "   source buildbridge_venv/bin/activate  # (or .venv/bin/activate)" >&2
    echo "   pip install -r requirements.txt" >&2
    exit 1
fi

echo "✅ Found virtual environment: $VENV_FOUND" >&2

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set Python path to include src directory
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

echo "🚀 Starting BuildBridge-MCP Server..." >&2
echo "📁 Working directory: $(pwd)" >&2
echo "🐍 Python executable: $(which python)" >&2
echo "📚 Python path: $PYTHONPATH" >&2
echo "" >&2
echo "Available MCP tools:" >&2
echo "- AI Query Processing: Ask questions about construction projects" >&2
echo "- Google Sheets Integration: Access live project data" >&2
echo "- Project Data Extraction: Flexible multi-sheet support" >&2
echo "" >&2
echo "Press Ctrl+C to stop the server" >&2
echo "" >&2

# Check for test mode argument
if [[ "${1:-}" == "--test" ]]; then
    echo "🧪 Running MCP server initialization test..." >&2
    START_TIME=$(date +%s.%3N)
    exec python src/main.py --test
fi

# Run the MCP server
exec python src/main.py
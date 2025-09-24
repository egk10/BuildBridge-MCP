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
    echo "❌ No virtual environment found. Please create one first."
    echo "💡 Try one of these commands:"
    echo "   python -m venv buildbridge_venv"
    echo "   python -m venv .venv"
    echo "   python -m venv venv"
    echo ""
    echo "Then activate and install dependencies:"
    echo "   source buildbridge_venv/bin/activate  # (or .venv/bin/activate)"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "✅ Found virtual environment: $VENV_FOUND"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set Python path to include src directory
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

echo "🚀 Starting BuildBridge-MCP Server..."
echo "📁 Working directory: $(pwd)"
echo "🐍 Python executable: $(which python)"
echo "📚 Python path: $PYTHONPATH"
echo ""
echo "Available MCP tools:"
echo "- AI Query Processing: Ask questions about construction projects"
echo "- Google Sheets Integration: Access live project data"
echo "- Project Data Extraction: Flexible multi-sheet support"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Check for test mode argument
if [[ "${1:-}" == "--test" ]]; then
    echo "🧪 Running MCP server initialization test..."
    START_TIME=$(date +%s.%3N)
    exec python src/main.py --test
fi

# Run the MCP server
exec python src/main.py
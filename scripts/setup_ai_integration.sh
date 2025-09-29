#!/bin/bash
"""
Quick Setup and Test Script for AI Integration
Installs dependencies and runs basic tests
"""

echo "🏗️ BuildBridge-MCP AI Integration Setup"
echo "========================================"

# Change to the script directory
cd "$(dirname "$0")"

echo "📦 Installing Python dependencies..."

# Check if virtual environment exists
if [ ! -d "construction_env" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv construction_env
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source construction_env/bin/activate

# Install/upgrade dependencies
echo "📥 Installing/upgrading packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "⚠️  OpenAI API Key not found!"
    echo "   To enable AI features, set your API key:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "🔄 Running tests without AI service..."
    python test_ai_integration.py --quick
else
    echo ""
    echo "✅ OpenAI API Key found!"
    echo "🔄 Running full test suite..."
    python test_ai_integration.py
fi

echo ""
echo "🚀 Setup complete! You can now:"
echo "   1. Set OPENAI_API_KEY environment variable for AI features"
echo "   2. Run: python production_mcp_integration.py --mode test"
echo "   3. Start server: python production_mcp_integration.py --mode server"
echo ""
#!/bin/bash
# ============================================================================
# Salesforce Flow Analyzer MCP Server - Startup Script
# ============================================================================
# This script starts the MCP server for use with Claude Desktop or other
# MCP-compatible clients.
# ============================================================================

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Salesforce Flow Analyzer MCP Server"
echo "================================================"
echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found at .venv/"
    echo "   Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if required packages are installed
echo "✅ Checking dependencies..."
python3 -c "import mcp; print(f'   MCP SDK version: {mcp.__version__}')" 2>/dev/null || {
    echo "❌ MCP SDK not installed. Installing..."
    pip install mcp>=1.0.0
}

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo ""
echo "🔧 Configuration:"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""
echo "📡 Starting MCP Server (stdio mode)..."
echo "   Press Ctrl+C to stop"
echo ""

# Run the MCP server
python3 -m mcp_server.server

#!/bin/bash
# ============================================================================
# Setup MCP Server for Claude Desktop
# ============================================================================
# This script automatically configures Claude Desktop to use the
# Salesforce Flow Analyzer MCP Server.
# ============================================================================

set -e

echo "🔧 Claude Desktop MCP Server Setup"
echo "===================================="
echo ""

# Detect OS and set config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "   Please manually configure Claude Desktop."
    exit 1
fi

echo "📁 Config location: $CONFIG_FILE"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python3"

# Check if Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python not found at: $PYTHON_PATH"
    echo "   Please create virtual environment first:"
    echo "   cd $PROJECT_ROOT && python3 -m venv .venv"
    exit 1
fi

echo "✅ Python found: $PYTHON_PATH"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  Existing config found at: $CONFIG_FILE"
    echo ""
    echo "Current config:"
    cat "$CONFIG_FILE"
    echo ""
    read -p "Do you want to backup and replace it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        echo "✅ Backup created: $BACKUP_FILE"
    else
        echo ""
        echo "To manually add the MCP server, merge this into your config:"
        echo ""
        echo '  "salesforce-flow-analyzer": {'
        echo "    \"command\": \"$PYTHON_PATH\","
        echo '    "args": ["-m", "mcp_server.server"],'
        echo "    \"cwd\": \"$PROJECT_ROOT\","
        echo '    "env": {'
        echo "      \"PYTHONPATH\": \"$PROJECT_ROOT\""
        echo '    }'
        echo '  }'
        echo ""
        exit 0
    fi
fi

# Create the configuration
cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "salesforce-flow-analyzer": {
      "command": "$PYTHON_PATH",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "$PROJECT_ROOT",
      "env": {
        "PYTHONPATH": "$PROJECT_ROOT"
      }
    }
  }
}
EOF

echo ""
echo "✅ Configuration written to: $CONFIG_FILE"
echo ""
echo "📋 Configuration content:"
cat "$CONFIG_FILE"
echo ""
echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Quit Claude Desktop completely (from menu bar)"
echo "  2. Reopen Claude Desktop"
echo "  3. Look for the 🔧 tools icon in the chat"
echo "  4. You should see 'salesforce-flow-analyzer' with 14 tools"
echo ""
echo "Try asking Claude:"
echo '  "What Salesforce Flow analysis tools do you have?"'
echo ""

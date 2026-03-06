# 🚀 MCP Server Deployment Guide

This guide explains how to deploy and use the Salesforce Flow Analyzer MCP Server with various LLM clients.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Claude Desktop Setup](#claude-desktop-setup)
3. [VS Code with Copilot Setup](#vs-code-with-copilot-setup)
4. [Standalone Server Mode](#standalone-server-mode)
5. [Available Tools](#available-tools)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **Python 3.10+** installed
2. **Virtual environment** set up with dependencies:
   ```bash
   cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r mcp_server/requirements.txt
   ```

3. **Environment variables** configured in `.env`:
   ```env
   GITHUB_TOKEN=your_github_token
   LLM_PROVIDER=github
   LLM_MODEL=gpt-4o
   ```

4. **Salesforce flows** fetched (optional):
   ```bash
   python3 cli/fetch_org_flows_cli.py
   ```

---

## Claude Desktop Setup

### Step 1: Locate Claude Desktop Config

The configuration file is located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 2: Add MCP Server Configuration

Open (or create) the config file and add:

```json
{
  "mcpServers": {
    "salesforce-flow-analyzer": {
      "command": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation/.venv/bin/python3",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation",
      "env": {
        "PYTHONPATH": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation"
      }
    }
  }
}
```

### Step 3: Copy Configuration (Quick Setup)

Run this command to automatically set up Claude Desktop:

```bash
# Create Claude config directory if it doesn't exist
mkdir -p ~/Library/Application\ Support/Claude

# Copy the configuration
cp /Users/saurabhyadav/Desktop/Flow_AI_Implementation/mcp_server/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or merge with existing config if you have other MCP servers:

```bash
# View existing config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Then manually merge the salesforce-flow-analyzer entry
```

### Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔧 tools icon in the chat interface
4. You should see "salesforce-flow-analyzer" with 14 tools available

### Step 5: Verify Connection

In Claude Desktop, ask:
> "What Salesforce Flow tools do you have available?"

Claude should list tools like `analyze_flow`, `list_flows`, `query_flow`, etc.

---

## VS Code with Copilot Setup

If you're using VS Code with GitHub Copilot Chat:

### Option 1: Use as Extension (Future)

MCP support in VS Code Copilot is still evolving. Check for updates.

### Option 2: Use via Terminal

You can run the interactive test directly:

```bash
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation
source .venv/bin/activate
python3 mcp_server/interactive_test.py
```

---

## Standalone Server Mode

### Running the Server Manually

```bash
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation
source .venv/bin/activate
python3 -m mcp_server.server
```

Or use the startup script:

```bash
./mcp_server/start_server.sh
```

### HTTP/SSE Mode (For Web Clients)

To run as an HTTP server (if you need web access):

```bash
# Install additional dependencies
pip install uvicorn starlette sse-starlette

# Run in SSE mode (modify server.py to add HTTP transport)
python3 -m mcp_server.server --transport sse --port 8000
```

---

## Available Tools

The MCP server exposes **14 tools** for Salesforce Flow analysis:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `analyze_flow` | Deep analysis of a flow | "Analyze the Create_property flow" |
| `list_flows` | List all available flows | "Show me all flows" |
| `query_flow` | Ask questions about a flow | "What triggers the offer_to_lead flow?" |
| `run_scenarios` | Run test scenarios | "Run tests on Create_property" |
| `create_baseline` | Create a baseline snapshot | "Create baseline for all flows" |
| `compare_baseline` | Compare against baseline | "Compare current vs baseline" |
| `run_regression` | Run regression tests | "Check for regressions" |
| `check_best_practices` | Audit best practices | "Check best practices for Create_property" |
| `get_flow_details` | Get flow metadata | "Show details of Case_Closed_chatter" |
| `list_scenarios` | List test scenarios | "What test scenarios exist?" |
| `create_scenarios` | Generate new scenarios | "Create scenarios for my flows" |
| `generate_report` | Generate HTML report | "Generate a test report" |
| `get_config_status` | Check configuration | "Show config status" |
| `search_flows` | Search for flows | "Search for flows with 'Account'" |

---

## Troubleshooting

### Server Won't Start

1. **Check Python path**:
   ```bash
   which python3
   # Should show: /Users/saurabhyadav/Desktop/Flow_AI_Implementation/.venv/bin/python3
   ```

2. **Check MCP SDK installed**:
   ```bash
   pip show mcp
   ```

3. **Check imports work**:
   ```bash
   python3 -c "from mcp_server.server import FlowAnalyzerMCPServer; print('OK')"
   ```

### Claude Desktop Doesn't Show Tools

1. **Check config file syntax**:
   ```bash
   python3 -c "import json; json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json'))"
   ```

2. **Check server logs**: Look at Claude Desktop's developer console

3. **Restart completely**: Quit Claude Desktop from menu bar, not just close window

### LLM Errors

1. **Check API token**:
   ```bash
   echo $GITHUB_TOKEN
   ```

2. **Test LLM connection**:
   ```bash
   python3 -c "from src.config import get_config; c=get_config(); c.print_status()"
   ```

### No Flows Found

Run the fetch script first:
```bash
python3 cli/fetch_org_flows_cli.py
```

---

## Example Conversations with Claude Desktop

Once configured, you can have conversations like:

**You**: "Analyze the Create_property flow and tell me what it does"

**You**: "What decisions does the offer_to_lead flow make?"

**You**: "Run all test scenarios for the Case_Closed_chatter flow"

**You**: "Check if the Opportunity_Won_Account_Priority_Actions flow follows best practices"

**You**: "Create a baseline of all my current flows"

**You**: "Search for any flows that interact with Account records"

---

## Support

For issues or questions:
- Check the [COMMANDS.md](../COMMANDS.md) for CLI alternatives
- Review server logs for error messages
- Ensure all dependencies are installed


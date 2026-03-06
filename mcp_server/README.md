# Salesforce Flow Analyzer MCP Server

A Model Context Protocol (MCP) server that exposes Salesforce Flow analysis, testing, and regression detection capabilities to AI assistants like Claude.

## 🎯 Features

| Tool | Description |
|------|-------------|
| `analyze_flow` | Comprehensive flow analysis with decisions, triggers, record operations |
| `list_flows` | List all available Salesforce Flows |
| `query_flow` | AI-powered natural language queries about flows |
| `create_scenarios` | Generate test scenarios from flow logic |
| `run_scenarios` | Execute AI-powered test scenarios |
| `create_baseline` | Create baseline snapshots for regression testing |
| `run_regression` | Compare flows against baselines |
| `check_best_practices` | Review flows against Salesforce best practices |
| `generate_report` | Generate HTML test reports |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation

# Install MCP SDK and dependencies
pip install -r mcp_server/requirements.txt

# Or install mcp directly
pip install mcp
```

### 2. Configure Claude Desktop

Add the server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "salesforce-flow-analyzer": {
      "command": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation/.venv/bin/python",
      "args": [
        "/Users/saurabhyadav/Desktop/Flow_AI_Implementation/mcp_server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation"
      }
    }
  }
}
```

> **Note:** Update the paths to match your installation location.

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

## 📖 Usage Examples

Once configured, you can ask Claude to use the Flow Analyzer tools:

### Analyze a Flow
```
"Analyze the Create_property flow and tell me about its decisions"
```

### Query Flow Logic
```
"What triggers the Lead_Communication_Flow and what conditions need to be met?"
```

### Run Best Practices Check
```
"Check the offer_to_lead flow against Salesforce best practices"
```

### Create Baseline & Run Regression
```
"Create a baseline of current flows, then run regression analysis"
```

### Generate Test Scenarios
```
"Run 5 test scenarios for the Opportunity_Won flow and show me the results"
```

## 🛠️ Available Tools

### Flow Analysis

#### `analyze_flow`
Analyze a Salesforce Flow with comprehensive insights.

**Parameters:**
- `flow_name` (required): Developer name of the flow
- `analysis_type` (optional): `full`, `decisions`, `triggers`, `records`, `screens`

#### `list_flows`
List all available flows in the workspace.

**Parameters:**
- `include_details` (optional): Include element counts and status

#### `query_flow`
Ask natural language questions about flows using AI.

**Parameters:**
- `query` (required): Your question
- `flow_name` (optional): Specific flow to query

### Scenario Testing

#### `create_scenarios`
Generate test scenarios from flow decision logic.

#### `run_scenarios`
Execute test scenarios against flows.

**Parameters:**
- `flow_name` (optional): Filter by flow
- `category` (optional): Filter by category
- `limit` (optional): Maximum scenarios to run

#### `list_scenario_categories`
List all available test scenario categories.

### Baseline & Regression

#### `create_baseline`
Create a baseline snapshot of current flows.

**Parameters:**
- `name` (optional): Baseline name
- `description` (optional): Description

#### `list_baselines`
List all available baselines.

#### `get_active_baseline`
Get the currently active baseline.

#### `run_regression`
Compare current flows against baseline.

**Parameters:**
- `baseline_id` (optional): Specific baseline to compare
- `flow_name` (optional): Compare only specific flow

### Utilities

#### `get_flow_dependencies`
Get all dependencies (objects, fields, Apex, subflows).

**Parameters:**
- `flow_name` (required): Flow to analyze

#### `check_best_practices`
Review flow against Salesforce best practices.

**Parameters:**
- `flow_name` (required): Flow to check

#### `generate_report`
Generate HTML test reports.

**Parameters:**
- `report_type` (optional): `scenario`, `regression`, `analysis`

#### `get_config_status`
Check LLM and Salesforce configuration.

## 📚 Resources

The server also exposes flows and reports as MCP resources:

- `flow://Create_property` - Access flow metadata
- `report://latest_report` - Access test reports

## 🔧 Environment Variables

The server uses the same `.env` configuration as the main project:

```env
# LLM Provider (github, openai, azure, anthropic)
LLM_PROVIDER=github
GITHUB_TOKEN=your_github_token
LLM_MODEL=gpt-4o

# Optional: Salesforce (if not using CLI auth)
SF_INSTANCE_URL=https://your-instance.my.salesforce.com
```

## 🐛 Troubleshooting

### Server Not Starting

1. Check Python path is correct
2. Ensure all dependencies are installed
3. Check the server logs

### Tools Not Working

1. Verify flows exist in `org_flows/` directory
2. Run `fetch_org_flows_cli.py` to fetch flows
3. Check LLM configuration with `get_config_status`

### Debug Mode

Run the server directly to see logs:

```bash
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation
python mcp_server/server.py
```

## 📁 Project Structure

```
mcp_server/
├── __init__.py           # Package initialization
├── server.py             # Main MCP server implementation
├── requirements.txt      # Python dependencies
├── mcp_manifest.json     # Server manifest
├── claude_desktop_config.json  # Sample Claude Desktop config
└── README.md             # This file
```

## 🔗 Related

- [Main Project README](../README.md)
- [Command Reference](../COMMANDS.md)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)

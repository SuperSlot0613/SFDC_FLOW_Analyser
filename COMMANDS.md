# 🚀 Flow AI Implementation - Complete Command Reference

> AI-powered Salesforce Flow Analysis & Regression Testing System

---

## 📋 Table of Contents
- [Setup & Configuration](#1-setup--configuration)
- [Fetch Flows from Salesforce](#2-fetch-flows-from-salesforce-org)
- [Analyze Flows](#3-analyze-flows)
- [Generate Scenarios](#4-generate-decision-based-scenarios)
- [Run AI Scenario Tests](#5-run-ai-scenario-tests)
- [Generate Reports](#6-generate-reports)
- [Query Flows with AI](#7-query-flows-with-ai)
- [Regression Testing](#8-regression-testing)
- [MCP Server](#9-mcp-server)
- [Utility Commands](#10-utility-commands)
- [Quick Start](#-quick-start-full-pipeline)

---

## 📁 Project Structure

```
Flow_AI_Implementation/
├── cli/                    # CLI tools
│   ├── fetch_org_flows_cli.py
│   ├── run_decision_scenarios.py
│   ├── create_decision_based_scenarios.py
│   └── generate_scenario_report.py
├── data/                   # Generated data files
│   ├── decision_based_scenarios.json
│   ├── flow_analyses.json
│   └── flow_model.pkl
├── scripts/                # High-level scripts
│   ├── salesforce_flow_agent.py
│   └── flow_ai_ml_model.py
├── mcp_server/             # MCP Server for Claude Desktop
│   └── server.py
├── src/                    # Core modules
│   ├── model.py
│   ├── config.py
│   ├── llm_integration.py
│   └── ...
├── org_flows/              # Salesforce flow metadata
├── flow_baselines/         # Baseline snapshots
└── reports/                # Generated reports
```

---

## 1. Setup & Configuration

```bash
# Navigate to project
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation

# Check configuration status
python3 -c "from src.config import get_config; c=get_config(); c.print_status()"
```

### Environment Variables (.env file)
```env
# GitHub Models (FREE with Copilot Pro - 50 requests/day)
GITHUB_TOKEN=your_github_token
LLM_PROVIDER=github
LLM_MODEL=gpt-4o

# Salesforce OAuth
SF_CLIENT_ID=your_client_id
SF_CLIENT_SECRET=your_client_secret
SF_USERNAME=your_username
SF_INSTANCE_URL=https://your-instance.my.salesforce.com
```

---

## 2. Fetch Flows from Salesforce Org

```bash
# Fetch all active flows from your org (requires SF CLI authentication)
python3 cli/fetch_org_flows_cli.py

# Authenticate to Salesforce (if not already)
sf org login web

# Check authenticated orgs
sf org list
```

**Output:**
- `org_flows/*.json` - Individual flow metadata files
- `org_flows/_all_flows.json` - Combined flows file
- `flow_baselines/` - Baseline snapshots

---

## 3. Analyze Flows

```bash
# Analyze all fetched flows and save to data/flow_analyses.json
python3 cli/create_decision_based_scenarios.py
```

**Output:**
- `data/flow_analyses.json` - Complete analysis of all flows with:
  - Decisions & rules
  - Record lookups, creates, updates
  - Apex integrations
  - Screen validations
  - Formulas & variables
  - Trigger conditions

---

## 4. Generate Decision-Based Scenarios

```bash
# Generate test scenarios from analyzed flows
python3 cli/create_decision_based_scenarios.py
```

**Output:**
- `data/decision_based_scenarios.json` - 87 scenarios across 17 categories:
  - Decision Logic Analysis
  - Null Value Handling
  - Default Path Analysis
  - Record Lookup Analysis
  - Empty Result Handling
  - Record Creation Analysis
  - Record Update Analysis
  - Apex Integration Analysis
  - Apex Fault Handling
  - Screen Validation Analysis
  - Screen Input Analysis
  - Formula Analysis
  - Decision Thresholds
  - Input/Output Variable Analysis
  - Flow Trigger Conditions
  - Flow Trigger Edge Cases

---

## 5. Run AI Scenario Tests

```bash
# Run all 87 scenarios (requires API quota)
python3 cli/run_decision_scenarios.py

# Run with HTML report generation
python3 cli/run_decision_scenarios.py --report

# Run limited scenarios (to save API quota)
python3 cli/run_decision_scenarios.py --limit 5

# Run specific category only
python3 cli/run_decision_scenarios.py --category "Decision Logic Analysis"

# Run for specific flow only
python3 cli/run_decision_scenarios.py --flow "Create_property"

# Combine options
python3 cli/run_decision_scenarios.py --flow "offer_to_lead" --category "Flow Trigger Conditions" --report
```

### Available Options:
| Flag | Description | Example |
|------|-------------|---------|
| `--report` | Generate HTML report after run | `--report` |
| `--limit N` | Run only N scenarios | `--limit 10` |
| `--category "X"` | Filter by category | `--category "Null Value Handling"` |
| `--flow "X"` | Filter by flow name | `--flow "Create_property"` |

---

## 6. Generate Reports

```bash
# Generate Allure-style HTML report from last run
python3 generate_scenario_report.py

# Open the scenario test report
open reports/scenario_report_*.html

# Open the project summary dashboard
open PROJECT_SUMMARY.html
```

### Report Files:
- `reports/scenario_report_YYYYMMDD_HHMMSS.html` - Detailed test results
- `PROJECT_SUMMARY.html` - Interactive dashboard with all flows & scenarios

---

## 7. Query Flows with AI

### Single Query
```bash
python3 -c "from src.model import create_model_from_config; m=create_model_from_config(); print(m.query('What triggers the offer_to_lead flow?'))"
```

### Query Specific Flow with Metadata
```bash
python3 -c "
from src.model import create_model_from_config
import json
m = create_model_from_config()
flow = json.load(open('org_flows/Create_property.json'))
print(m.query('What decisions does this flow have?', flow_metadata=flow))
"
```

### Example Queries:
```bash
# Ask about trigger conditions
python3 -c "from src.model import create_model_from_config; m=create_model_from_config(); print(m.query('When does the Lead Communication Flow trigger?'))"

# Ask about decision logic
python3 -c "from src.model import create_model_from_config; m=create_model_from_config(); print(m.query('What happens when Amount >= 100000 in Opportunity flow?'))"

# Ask about record operations
python3 -c "from src.model import create_model_from_config; m=create_model_from_config(); print(m.query('What fields are set when creating a Lead in offer_to_lead?'))"
```

---

## 8. Regression Testing

```bash
# Run regression tests against baseline
python3 demo_regression.py

# Create a new baseline
python3 -c "from src.baseline_manager import BaselineManager; b=BaselineManager(); print(b.create_baseline('org_flows'))"

# List existing baselines
ls -la flow_baselines/

# Compare current flows with specific baseline
python3 -c "
from src.baseline_manager import BaselineManager
b = BaselineManager()
baseline_id = 'baseline_20260228_200018_5ae162'  # Replace with your baseline
diff = b.compare_with_baseline(baseline_id, 'org_flows')
print(diff)
"
```

---

## 9. MCP Server (Model Context Protocol)

The MCP Server exposes all Flow Analyzer functionality to Claude Desktop and other MCP clients.

### Start MCP Server
```bash
# Run the MCP server
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation
source .venv/bin/activate
python3 -m mcp_server.server
```

### Configure Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "salesforce-flow-analyzer": {
      "command": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation/.venv/bin/python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation",
      "env": {
        "PYTHONPATH": "/Users/saurabhyadav/Desktop/Flow_AI_Implementation"
      }
    }
  }
}
```

### Available MCP Tools
- `analyze_flow` - Analyze a Salesforce Flow
- `list_flows` - List all available flows
- `query_flow` - Ask questions about a flow
- `run_scenarios` - Run test scenarios
- `create_baseline` - Create a baseline snapshot
- `compare_baseline` - Compare against baseline
- `run_regression` - Run regression tests
- `check_best_practices` - Check flow best practices
- `get_flow_details` - Get detailed flow information
- `list_scenarios` - List available scenarios
- `create_scenarios` - Generate test scenarios
- `generate_report` - Generate HTML report
- `get_config_status` - Check configuration
- `search_flows` - Search for flows

---

## 10. Utility Commands

### View Project Statistics
```bash
# List all flows in org_flows directory
ls -la org_flows/

# View flow analyses summary
python3 -c "import json; d=json.load(open('data/flow_analyses.json')); print(f'Flows: {len(d[\"flows\"])}')"

# View scenario count
python3 -c "import json; d=json.load(open('data/decision_based_scenarios.json')); print(f'Scenarios: {d[\"total_scenarios\"]} across {len(d[\"categories\"])} categories')"

# List all categories
python3 -c "import json; d=json.load(open('data/decision_based_scenarios.json')); [print(f'  • {c}') for c in d['categories']]"
```

### Check API Rate Limit
```bash
# Test if API quota is available (GitHub Models: 50/day)
python3 -c "from src.model import create_model_from_config; m=create_model_from_config(); print(m.query('test'))"
```

### View Flow Details
```bash
# Pretty print a flow's JSON
python3 -c "import json; print(json.dumps(json.load(open('org_flows/Create_property.json')), indent=2))" | head -100

# Count elements in a flow
python3 -c "
import json
f = json.load(open('data/flow_analyses.json'))
for flow in f['flows']:
    print(f\"{flow['flow_name']}: {len(flow.get('decisions',[]))} decisions, {len(flow.get('record_creates',[]))} creates\")
"
```

---

## ⚡ Quick Start (Full Pipeline)

Run these commands in sequence to execute the complete workflow:

```bash
# Navigate to project
cd /Users/saurabhyadav/Desktop/Flow_AI_Implementation

# Step 1: Fetch flows from Salesforce org
python3 cli/fetch_org_flows_cli.py

# Step 2: Generate decision-based test scenarios (also analyzes flows)
python3 cli/create_decision_based_scenarios.py

# Step 3: Run AI scenario tests with report (when API quota available)
python3 cli/run_decision_scenarios.py --report

# Step 4: View results
open PROJECT_SUMMARY.html
open reports/scenario_report_*.html
```

---

## ⚠️ Important Notes

### Rate Limits
| Provider | Limit | Reset |
|----------|-------|-------|
| GitHub Models | 50 requests/day | Every 24 hours |
| OpenAI | Based on tier | Varies |
| Azure OpenAI | Based on deployment | Varies |

### Prerequisites
- **Python 3.x** - No external dependencies required!
- **Salesforce CLI** - Must be authenticated (`sf org login web`)
- **GitHub Token** - For GitHub Models (FREE with Copilot Pro)

### File Structure
```
Flow_AI_Implementation/
├── src/
│   ├── model.py          # Unified AI model
│   ├── analyzer.py       # Flow analyzer
│   ├── config.py         # Configuration
│   ├── baseline_manager.py
│   └── api.py            # REST API
├── org_flows/            # Fetched flow metadata
├── flow_baselines/       # Baseline snapshots
├── reports/              # Generated HTML reports
├── flow_analyses.json    # Analyzed flow data
├── decision_based_scenarios.json  # Test scenarios
├── PROJECT_SUMMARY.html  # Interactive dashboard
├── .env                  # Configuration
└── COMMANDS.md           # This file
```

---

## 📊 Project Statistics

| Metric | Count |
|--------|-------|
| Total Flows | 11 |
| Test Scenarios | 87 |
| Categories | 17 |
| Decision Points | 14 |
| Triggered Flows | 7 |

---

## 🔗 Quick Links

- **Dashboard**: `open PROJECT_SUMMARY.html`
- **Latest Report**: `open reports/scenario_report_*.html`
- **Flow Files**: `ls org_flows/`
- **Configuration**: `cat .env`

---

## 11. AI Agent (New!)

The project now includes a **standalone AI Agent** that encapsulates all functionality.

### Using as Python Library
```python
from salesforce_flow_agent import SalesforceFlowAgent, create_agent, quick_query

# Create agent
agent = SalesforceFlowAgent(verbose=True)

# Analyze a flow
result = agent.analyze_flow("org_flows/Create_property.json")
print(result.to_json())

# Query with AI
answer = agent.query("What triggers this flow?", flow_name="offer_to_lead")
print(answer.response)

# Validate best practices
insights = agent.validate_flow("org_flows/Create_property.json")
for i in insights:
    print(f"[{i.severity}] {i.message}")

# Detect regressions
changes = agent.detect_regression()

# Run scenarios
results = agent.run_scenarios(limit=10)

# Generate report
report_path = agent.generate_report(results)

# Quick functions (no agent needed)
response = quick_query("What does Create Property do?")
analysis = quick_analyze("org_flows/Create_property.json")
```

### Using as CLI Tool
```bash
# Analyze flows
python3 salesforce_flow_agent.py analyze --flow org_flows/Create_property.json
python3 salesforce_flow_agent.py analyze --all

# Query with AI
python3 salesforce_flow_agent.py query "What triggers the offer_to_lead flow?"
python3 salesforce_flow_agent.py query "What decisions exist?" --flow Create_property

# Validate flows
python3 salesforce_flow_agent.py validate --flow org_flows/Create_property.json

# Run scenario tests
python3 salesforce_flow_agent.py test --limit 10
python3 salesforce_flow_agent.py test --category "Decision Logic Analysis" --report

# Detect regressions
python3 salesforce_flow_agent.py regression
python3 salesforce_flow_agent.py regression --baseline baseline_20260228_200018_5ae162
```

### Agent Capabilities (10 Total)
| # | Capability | Method | Description |
|---|------------|--------|-------------|
| 1 | **Flow Analysis** | `analyze_flow()` | Extract decisions, triggers, records, screens |
| 2 | **Natural Language Query** | `query()` | Ask questions about flows |
| 3 | **Regression Detection** | `detect_regression()` | Compare with baselines |
| 4 | **Scenario Testing** | `run_scenarios()` | Execute test scenarios |
| 5 | **Report Generation** | `generate_report()` | Create HTML reports |
| 6 | **Improvement Suggestions** | `suggest_improvements()` | AI recommendations |
| 7 | **Flow Validation** | `validate_flow()` | Best practices check |
| 8 | **Flow Explanation** | `explain_flow()` | Human-readable summary |
| 9 | **Flow Comparison** | `compare_flows()` | Diff two flows |
| 10 | **Impact Prediction** | `predict_impact()` | Analyze change impact |

---

## 12. AI/ML Model (Advanced!)

A comprehensive **trainable AI/ML Model** for Salesforce Flow analysis with embeddings, pattern learning, and inference.

### Training the Model
```bash
# Train model on all flows
python3 flow_ai_ml_model.py train --flows-dir org_flows --output flow_model.pkl

# Train with multiple epochs
python3 flow_ai_ml_model.py train --flows-dir org_flows --epochs 10 --output flow_model.pkl
```

### Making Predictions
```bash
# Predict/analyze a specific flow
python3 flow_ai_ml_model.py predict --model flow_model.pkl --flow "org_flows/Case_Closed_chatter.json"

# Predict with detailed analysis
python3 flow_ai_ml_model.py predict --model flow_model.pkl --flow "org_flows/Create_property.json"
```

### Natural Language Query
```bash
# Ask questions about flows
python3 flow_ai_ml_model.py query --model flow_model.pkl "What flows update Account records?"
python3 flow_ai_ml_model.py query --model flow_model.pkl "How many decision points are there?"
python3 flow_ai_ml_model.py query --model flow_model.pkl "Which flows are triggered on Case?"

# Query with flow context
python3 flow_ai_ml_model.py query --model flow_model.pkl --flow "org_flows/Create_property.json" "What does this flow do?"
```

### Generate Scenarios
```bash
# Generate test scenarios from flows
python3 flow_ai_ml_model.py generate --flows-dir org_flows --output generated_scenarios.json
```

### Export Model
```bash
# Export model to JSON for inspection/portability
python3 flow_ai_ml_model.py export --model flow_model.pkl --output model_export.json
```

### Using as Python Library
```python
from flow_ai_ml_model import SalesforceFlowAIModel

# Create and train model
model = SalesforceFlowAIModel()
flows = model._load_flows_from_directory("org_flows")
metrics = model.train(flows, epochs=5)
print(f"Training accuracy: {metrics['accuracy']}")

# Save trained model
model.save("my_model.pkl")

# Load trained model
model = SalesforceFlowAIModel.load("my_model.pkl")

# Make predictions
prediction = model.predict("flow_analysis", flow_data)
print(f"Complexity: {prediction.result['complexity']}")
print(f"Confidence: {prediction.confidence}%")

# Query the model
response = model.query("What decisions exist?", flow_context)
print(response.response)

# Generate embeddings
embedding = model.embed(flow_data)
print(f"Embedding dimensions: {len(embedding)}")

# Compare flow similarity
similarity = model.similarity(flow1, flow2)
print(f"Flows are {similarity*100:.1f}% similar")
```

### Model Architecture
| Component | Purpose |
|-----------|---------|
| **FeatureExtractor** | Extract 50+ features from flow metadata |
| **FlowEmbedding** | Generate 128-dim vector representations |
| **PatternLearner** | Learn decision, trigger, and object patterns |
| **RuleEngine** | 25+ built-in analysis rules |
| **NLQProcessor** | Natural language query understanding |
| **ScenarioGenerator** | Generate test scenarios from patterns |
| **AnomalyDetector** | Detect unusual flow patterns |

### Model Capabilities
| # | Capability | Method | Description |
|---|------------|--------|-------------|
| 1 | **Training** | `train()` | Learn from flow corpus |
| 2 | **Prediction** | `predict()` | Analyze flow complexity |
| 3 | **Embeddings** | `embed()` | Generate vector representations |
| 4 | **Similarity** | `similarity()` | Compare two flows |
| 5 | **Query** | `query()` | Natural language questions |
| 6 | **Rules** | `apply_rules()` | Run analysis rules |
| 7 | **Scenarios** | `generate_scenarios()` | Create test scenarios |
| 8 | **Anomaly** | `detect_anomalies()` | Find unusual patterns |
| 9 | **Export** | `export_to_json()` | Serialize model |
| 10 | **Load/Save** | `save()/load()` | Persist model |

### Example Output - Prediction
```json
{
  "flow_type": "RecordTriggeredFlow",
  "complexity": 45.5,
  "elements": {
    "decisions": 3,
    "record_lookups": 2,
    "record_creates": 1,
    "record_updates": 2
  },
  "triggers": {
    "type": "RecordAfterSave",
    "object": "Opportunity",
    "conditions": [
      {"field": "IsWon", "operator": "EqualTo", "value": "true"}
    ]
  },
  "similar_patterns": [
    "decision_EqualTo_IsWon",
    "trigger_RecordAfterSave_Opportunity"
  ]
}
```

---

*Generated for Flow AI Implementation Project*
*Last Updated: February 28, 2026*

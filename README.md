# Salesforce Metadata AI Model

A comprehensive AI-powered model for analyzing Salesforce metadata including Flows, Apex classes, and custom objects. The model can work standalone (rule-based) or enhanced with LLM capabilities.

## 🎯 Key Capabilities

| Task | Description |
|------|-------------|
| **Flow Analysis** | Parse structure, elements, decisions, execution paths |
| **Code Review** | Best practices, issues, quality assessment |
| **Security Review** | Vulnerabilities, data access patterns, compliance |
| **Dependency Mapping** | Objects, Fields, Apex classes, Subflows |
| **Impact Analysis** | Change risk assessment, downstream effects |
| **Optimization** | Performance, governor limits, recommendations |
| **Documentation** | Auto-generated technical and business docs |
| **Natural Language** | Ask questions about your metadata (with LLM) |

## 🚀 Quick Start

### Basic Usage (No Dependencies Required)

```python
from src.model import create_model, TaskType

# Create the model
model = create_model()

# Load your metadata
import json
with open('flow.json') as f:
    flow_data = json.load(f)

# Analyze
result = model.analyze(flow_data, TaskType.FLOW_ANALYSIS)
print(result.to_markdown())
```

### With LLM Enhancement

```python
# With OpenAI
model = create_model(llm_provider='openai')

# With Azure OpenAI
model = create_model(
    llm_provider='azure',
    endpoint='https://your-resource.openai.azure.com',
    deployment_name='your-deployment'
)

# With Anthropic Claude
model = create_model(llm_provider='anthropic')
```

### CLI Usage

```bash
# Analyze a flow
python src/main.py analyze flow.json

# Run the model directly
python src/model.py flow.json

# Run the demo
python demo_model.py
```

## 📊 Available Tasks

```python
from src.model import TaskType

# All available tasks:
TaskType.FLOW_ANALYSIS      # Comprehensive flow analysis
TaskType.CODE_REVIEW        # Best practices review
TaskType.SECURITY_REVIEW    # Security assessment
TaskType.DEPENDENCY_MAPPING # Map all dependencies
TaskType.IMPACT_ANALYSIS    # Change impact assessment
TaskType.OPTIMIZATION       # Performance recommendations
TaskType.DOCUMENTATION      # Generate documentation
TaskType.CUSTOM_QUERY       # Natural language queries (LLM)
```

## Project Structure

```
Flow_AI_Implementation/
├── src/
│   ├── main.py                      # CLI and main entry point
│   ├── salesforce_metadata_analyzer.py  # Core Flow analysis
│   ├── llm_integration.py           # LLM provider integrations
│   ├── metadata_extractor.py        # Salesforce metadata extraction
│   └── dependency_analyzer.py       # Dependency graph & impact analysis
├── IFB_CC_POSIDEX_AutoClose.json    # Sample Flow metadata
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## Analysis Capabilities

### 1. Flow Structure Analysis
- Trigger configuration (object, conditions, timing)
- Decision elements and branching logic
- Actions (Apex calls, record operations, subflows)
- Execution paths

### 2. Dependency Analysis
- Objects and Fields used
- Apex classes invoked
- Subflows called
- Cross-flow dependencies

### 3. Best Practices Review
- Governor limit concerns (DML in loops)
- Error handling coverage
- Hardcoded values detection
- API version recommendations

### 4. Impact Analysis
- Change impact assessment
- Downstream effects identification
- Risk level calculation
- Testing recommendations

### 5. Documentation Generation
- Technical specifications
- Business process descriptions
- Dependency diagrams (Mermaid format)
- Testing guides

## LLM Analysis Features

When integrated with an LLM, you get enhanced capabilities:

- **Natural Language Summaries**: Business-friendly explanations
- **Deep Code Review**: Security and performance analysis
- **Optimization Suggestions**: Specific, actionable recommendations
- **Custom Analysis**: Ask any question about your metadata

## Output Formats

- **Markdown**: Human-readable reports
- **JSON**: Structured data for integration
- **Mermaid**: Dependency diagrams
- **LLM Prompts**: Ready-to-use prompts for AI analysis

## License

MIT License

"""
Salesforce Metadata AI Analyzer
================================
A comprehensive toolkit for analyzing Salesforce metadata with AI/LLM integration.

Quick Start:
    from src import SalesforceMetadataAIModel, TaskType, create_model
    
    model = create_model()  # Rule-based
    # or
    model = create_model(llm_provider='openai')  # With LLM
    
    result = model.analyze(flow_metadata, TaskType.FLOW_ANALYSIS)
"""

# Core analyzers
from .salesforce_metadata_analyzer import (
    FlowAnalyzer,
    FlowAnalysis,
    FlowElement,
    AIMetadataInsights,
    SalesforceMetadataParser,
    analyze_flow_file
)

# Dependency analysis
from .dependency_analyzer import (
    DependencyGraph,
    Dependency,
    DependencyNode,
    FlowDependencyExtractor,
    ImpactAnalyzer,
    build_dependency_graph
)

# Configuration
from .config import (
    Config,
    get_config
)

# Unified AI Model
from .model import (
    SalesforceMetadataAIModel,
    TaskType,
    MetadataType,
    Severity,
    AnalysisResult,
    Issue,
    create_model,
    create_model_from_config
)

# Baseline Management
from .baseline_manager import (
    BaselineManager,
    BaselineMetadata,
    BaselineStatus
)

# Regression Analysis
from .regression_analyzer import (
    RegressionAnalyzer,
    RegressionReport,
    FlowComparison,
    FlowChange,
    ChangeType,
    ChangeSeverity,
    UpdateDecision
)

# Salesforce Client
from .salesforce_client import (
    SalesforceClient,
    MockSalesforceClient,
    SalesforceConnection,
    create_salesforce_client,
    authenticate_oauth,
    SalesforceAPIError
)

__version__ = "1.0.0"
__all__ = [
    # Unified AI Model (recommended)
    "SalesforceMetadataAIModel",
    "TaskType",
    "MetadataType", 
    "Severity",
    "AnalysisResult",
    "Issue",
    "create_model",
    "create_model_from_config",
    
    # Configuration
    "Config",
    "get_config",
    
    # Baseline Management
    "BaselineManager",
    "BaselineMetadata",
    "BaselineStatus",
    
    # Regression Analysis
    "RegressionAnalyzer",
    "RegressionReport",
    "FlowComparison",
    "FlowChange",
    "ChangeType",
    "ChangeSeverity",
    "UpdateDecision",
    
    # Salesforce Client
    "SalesforceClient",
    "MockSalesforceClient",
    "SalesforceConnection",
    "create_salesforce_client",
    "authenticate_oauth",
    "SalesforceAPIError",
    
    # Core analyzers
    "FlowAnalyzer",
    "FlowAnalysis", 
    "FlowElement",
    "AIMetadataInsights",
    "SalesforceMetadataParser",
    "analyze_flow_file",
    
    # Dependency analysis
    "DependencyGraph",
    "Dependency",
    "DependencyNode",
    "FlowDependencyExtractor",
    "ImpactAnalyzer",
    "build_dependency_graph",
]

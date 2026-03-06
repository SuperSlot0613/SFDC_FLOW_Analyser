"""
Salesforce Flow AI Agent
========================
A standalone AI-powered agent for Salesforce Flow analysis, testing, and regression detection.

This agent can be:
1. Used as a Python library
2. Run as a CLI tool
3. Deployed as an API service
4. Integrated into CI/CD pipelines

Author: Flow AI Implementation
Version: 1.0.0
"""

import json
import os
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add parent directory and src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import internal modules
from src.config import get_config, Config
from src.salesforce_metadata_analyzer import FlowAnalyzer
from src.baseline_manager import BaselineManager


class AnalysisType(Enum):
    """Types of analysis the agent can perform"""
    FULL = "full"                    # Complete flow analysis
    DECISIONS = "decisions"          # Decision logic only
    TRIGGERS = "triggers"            # Trigger conditions only
    RECORDS = "records"              # Record operations only
    SCREENS = "screens"              # Screen elements only
    REGRESSION = "regression"        # Compare with baseline
    SCENARIO = "scenario"            # Run test scenarios


@dataclass
class FlowInsight:
    """Represents an insight discovered from flow analysis"""
    category: str
    severity: str  # info, warning, critical
    message: str
    element: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of a flow analysis"""
    flow_name: str
    flow_type: str
    timestamp: str
    success: bool
    insights: List[FlowInsight] = field(default_factory=list)
    decisions: List[Dict] = field(default_factory=list)
    record_operations: List[Dict] = field(default_factory=list)
    triggers: List[Dict] = field(default_factory=list)
    screens: List[Dict] = field(default_factory=list)
    ai_summary: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass 
class QueryResult:
    """Result of an AI query"""
    query: str
    response: str
    flow_context: Optional[str] = None
    confidence: float = 1.0
    sources: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScenarioResult:
    """Result of a scenario test"""
    scenario_id: str
    category: str
    flow: str
    query: str
    expected: List[str]
    actual_response: str
    passed: bool
    matched_expectations: List[str] = field(default_factory=list)
    missing_expectations: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


class SalesforceFlowAgent:
    """
    AI-powered Salesforce Flow Analysis Agent
    
    Capabilities:
    1. analyze_flow() - Analyze flow metadata and extract insights
    2. query() - Ask natural language questions about flows
    3. detect_regression() - Compare flows against baselines
    4. run_scenarios() - Execute test scenarios
    5. generate_report() - Create HTML reports
    6. suggest_improvements() - AI-powered recommendations
    7. validate_flow() - Check for best practices violations
    8. explain_flow() - Generate human-readable explanations
    9. compare_flows() - Compare two flows
    10. predict_impact() - Predict impact of flow changes
    
    Usage:
        agent = SalesforceFlowAgent()
        
        # Analyze a flow
        result = agent.analyze_flow("path/to/flow.json")
        
        # Ask questions
        answer = agent.query("What triggers this flow?", flow_name="MyFlow")
        
        # Run regression detection
        changes = agent.detect_regression("baseline_id")
        
        # Run test scenarios
        results = agent.run_scenarios(limit=10)
    """
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        config: Optional[Config] = None,
        flows_dir: str = "org_flows",
        baselines_dir: str = "flow_baselines",
        reports_dir: str = "reports",
        verbose: bool = False
    ):
        """
        Initialize the Salesforce Flow AI Agent
        
        Args:
            config: Optional configuration object
            flows_dir: Directory containing flow JSON files
            baselines_dir: Directory for baseline storage
            reports_dir: Directory for generated reports
            verbose: Enable verbose output
        """
        self.config = config or get_config()
        self.flows_dir = Path(flows_dir)
        self.baselines_dir = Path(baselines_dir)
        self.reports_dir = Path(reports_dir)
        self.verbose = verbose
        
        # Initialize components
        self._analyzer_class = FlowAnalyzer
        self.baseline_manager = BaselineManager(str(self.baselines_dir))
        self._llm = None
        
        # Cache for loaded flows
        self._flow_cache: Dict[str, Dict] = {}
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        
        # Ensure directories exist
        self.flows_dir.mkdir(exist_ok=True)
        self.baselines_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        if self.verbose:
            print(f"🤖 Salesforce Flow AI Agent v{self.VERSION} initialized")
            print(f"   Flows: {self.flows_dir}")
            print(f"   Baselines: {self.baselines_dir}")
            print(f"   Reports: {self.reports_dir}")
    
    @property
    def llm(self):
        """Lazy-load the LLM model"""
        if self._llm is None:
            from src.model import create_model_from_config
            self._llm = create_model_from_config()
        return self._llm
    
    # =========================================================================
    # CAPABILITY 1: Flow Analysis
    # =========================================================================
    
    def analyze_flow(
        self,
        flow_path: Union[str, Path],
        analysis_type: AnalysisType = AnalysisType.FULL
    ) -> AnalysisResult:
        """
        Analyze a Salesforce Flow and extract insights
        
        Args:
            flow_path: Path to flow JSON file or flow name
            analysis_type: Type of analysis to perform
            
        Returns:
            AnalysisResult with extracted information and insights
        """
        try:
            # Load flow
            flow_data = self._load_flow(flow_path)
            flow_name = self._extract_flow_name(flow_data)
            
            # Check cache
            cache_key = f"{flow_name}_{analysis_type.value}"
            if cache_key in self._analysis_cache:
                return self._analysis_cache[cache_key]
            
            # Analyze flow directly
            analysis = self._parse_flow_metadata(flow_data)
            
            # Build result
            result = AnalysisResult(
                flow_name=analysis.get('flow_name', flow_name),
                flow_type=analysis.get('process_type', 'Unknown'),
                timestamp=datetime.now().isoformat(),
                success=True,
                decisions=analysis.get('decisions', []),
                record_operations=self._extract_record_ops(analysis),
                triggers=analysis.get('trigger_conditions', []),
                screens=analysis.get('screens', [])
            )
            
            # Generate insights
            result.insights = self._generate_insights(analysis)
            
            # Cache result
            self._analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return AnalysisResult(
                flow_name=str(flow_path),
                flow_type="Unknown",
                timestamp=datetime.now().isoformat(),
                success=False,
                error=str(e)
            )
    
    def analyze_all_flows(self) -> List[AnalysisResult]:
        """Analyze all flows in the flows directory"""
        results = []
        for flow_file in self.flows_dir.glob("*.json"):
            if flow_file.name.startswith("_"):
                continue
            result = self.analyze_flow(flow_file)
            results.append(result)
        return results
    
    # =========================================================================
    # CAPABILITY 2: Natural Language Query
    # =========================================================================
    
    def query(
        self,
        question: str,
        flow_name: Optional[str] = None,
        flow_metadata: Optional[Dict] = None,
        include_context: bool = True
    ) -> QueryResult:
        """
        Ask a natural language question about flows
        
        Args:
            question: The question to ask
            flow_name: Optional specific flow to query about
            flow_metadata: Optional flow metadata to include
            include_context: Whether to include flow context
            
        Returns:
            QueryResult with the AI response
        """
        try:
            # Build context
            context_flow = None
            if flow_metadata:
                context_flow = flow_metadata
            elif flow_name:
                context_flow = self._load_flow(flow_name)
            
            # Query LLM
            response = self.llm.query(question, flow_metadata=context_flow)
            
            return QueryResult(
                query=question,
                response=response,
                flow_context=flow_name,
                sources=[flow_name] if flow_name else []
            )
            
        except Exception as e:
            return QueryResult(
                query=question,
                response=f"Error: {str(e)}",
                confidence=0.0
            )
    
    def explain_flow(self, flow_path: Union[str, Path]) -> str:
        """
        Generate a human-readable explanation of a flow
        
        Args:
            flow_path: Path to flow or flow name
            
        Returns:
            Natural language explanation of the flow
        """
        flow_data = self._load_flow(flow_path)
        flow_name = self._extract_flow_name(flow_data)
        
        prompt = f"""Provide a comprehensive explanation of the Salesforce Flow '{flow_name}'.
        
Include:
1. What the flow does (purpose)
2. When it triggers (if record-triggered)
3. Key decision points
4. What records it creates/updates
5. Any integrations (Apex, emails, etc.)

Be clear and concise, suitable for a business user."""
        
        result = self.query(prompt, flow_metadata=flow_data)
        return result.response
    
    # =========================================================================
    # CAPABILITY 3: Regression Detection
    # =========================================================================
    
    def detect_regression(
        self,
        baseline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare current flows against a baseline to detect changes
        
        Args:
            baseline_id: Specific baseline to compare against (latest if None)
            
        Returns:
            Dictionary with added, removed, and modified flows
        """
        # Get baseline
        if baseline_id:
            baseline = self.baseline_manager.get_baseline(baseline_id)
        else:
            baseline = self.baseline_manager.get_active_baseline()
        
        if not baseline:
            return {"error": "No baseline found", "baselines_available": [
                b.baseline_id for b in self.baseline_manager.get_baseline_history()
            ]}
        
        # Get current flows
        current_flows = {}
        for flow_file in self.flows_dir.glob("*.json"):
            if flow_file.name.startswith("_"):
                continue
            try:
                with open(flow_file) as f:
                    flow_data = json.load(f)
                    name = flow_data.get('FullName', flow_file.stem)
                    current_flows[name] = flow_data
            except:
                pass
        
        # Get baseline flows (convert list to dict by name)
        baseline_flows_list = baseline.get('flows', [])
        baseline_flows = {}
        for flow in baseline_flows_list:
            name = flow.get('FullName', flow.get('name', 'Unknown'))
            baseline_flows[name] = flow
        
        # Compare
        added = [n for n in current_flows if n not in baseline_flows]
        removed = [n for n in baseline_flows if n not in current_flows]
        modified = []
        
        for name in current_flows:
            if name in baseline_flows:
                # Simple comparison - check if Metadata changed
                curr_meta = current_flows[name].get('Metadata', {})
                base_meta = baseline_flows[name].get('Metadata', {})
                if curr_meta != base_meta:
                    modified.append(name)
        
        return {
            "baseline_id": baseline.get('id', baseline_id),
            "baseline_created": baseline.get('created_at', 'Unknown'),
            "current_flow_count": len(current_flows),
            "baseline_flow_count": len(baseline_flows),
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": len(current_flows) - len(added) - len(modified)
        }
    
    def create_baseline(self, name: Optional[str] = None) -> str:
        """
        Create a new baseline from current flows
        
        Args:
            name: Optional name for the baseline
            
        Returns:
            Baseline ID
        """
        return self.baseline_manager.create_baseline(str(self.flows_dir), name)
    
    # =========================================================================
    # CAPABILITY 4: Scenario Testing
    # =========================================================================
    
    def run_scenarios(
        self,
        scenarios_file: str = "decision_based_scenarios.json",
        limit: Optional[int] = None,
        category: Optional[str] = None,
        flow_filter: Optional[str] = None
    ) -> List[ScenarioResult]:
        """
        Run test scenarios against the AI model
        
        Args:
            scenarios_file: Path to scenarios JSON file
            limit: Maximum number of scenarios to run
            category: Filter by category
            flow_filter: Filter by flow name
            
        Returns:
            List of ScenarioResult objects
        """
        results = []
        
        # Load scenarios
        with open(scenarios_file) as f:
            data = json.load(f)
        
        scenarios = data.get('scenarios', [])
        
        # Apply filters
        if category:
            scenarios = [s for s in scenarios if s['category'] == category]
        if flow_filter:
            scenarios = [s for s in scenarios if flow_filter.lower() in s['flow'].lower()]
        if limit:
            scenarios = scenarios[:limit]
        
        # Load flow analyses for context
        flow_analyses = {}
        if os.path.exists("flow_analyses.json"):
            with open("flow_analyses.json") as f:
                analyses = json.load(f)
                for flow in analyses.get('flows', []):
                    flow_analyses[flow['developer_name']] = flow
        
        # Run each scenario
        for scenario in scenarios:
            start_time = datetime.now()
            
            try:
                # Get flow context
                flow_data = flow_analyses.get(scenario['flow'])
                
                # Query the model
                response = self.llm.query(
                    scenario['query'],
                    flow_metadata=flow_data
                )
                
                # Validate response
                matched, missing = self._validate_response(
                    response,
                    scenario['expected_analysis']
                )
                
                passed = len(missing) == 0
                
                result = ScenarioResult(
                    scenario_id=scenario['id'],
                    category=scenario['category'],
                    flow=scenario['flow'],
                    query=scenario['query'],
                    expected=scenario['expected_analysis'],
                    actual_response=response,
                    passed=passed,
                    matched_expectations=matched,
                    missing_expectations=missing,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                
            except Exception as e:
                result = ScenarioResult(
                    scenario_id=scenario['id'],
                    category=scenario['category'],
                    flow=scenario['flow'],
                    query=scenario['query'],
                    expected=scenario['expected_analysis'],
                    actual_response="",
                    passed=False,
                    error=str(e),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            results.append(result)
            
            if self.verbose:
                status = "✅" if result.passed else "❌"
                print(f"{status} {scenario['id'][:50]}...")
        
        return results
    
    # =========================================================================
    # CAPABILITY 5: Report Generation
    # =========================================================================
    
    def generate_report(
        self,
        scenario_results: Optional[List[ScenarioResult]] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate an HTML report
        
        Args:
            scenario_results: Optional scenario results to include
            output_file: Output file path
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.reports_dir / f"agent_report_{timestamp}.html"
        
        # Generate report HTML
        html = self._generate_report_html(scenario_results)
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        return str(output_file)
    
    # =========================================================================
    # CAPABILITY 6: Improvement Suggestions
    # =========================================================================
    
    def suggest_improvements(self, flow_path: Union[str, Path]) -> List[FlowInsight]:
        """
        Generate AI-powered improvement suggestions for a flow
        
        Args:
            flow_path: Path to flow or flow name
            
        Returns:
            List of improvement suggestions
        """
        flow_data = self._load_flow(flow_path)
        flow_name = self._extract_flow_name(flow_data)
        
        prompt = f"""Analyze the Salesforce Flow '{flow_name}' and suggest improvements.

Consider:
1. Performance optimizations
2. Error handling improvements
3. Best practice violations
4. Maintainability issues
5. Security concerns

Format each suggestion as:
- Category: [category]
- Severity: [info/warning/critical]
- Issue: [description]
- Recommendation: [how to fix]"""
        
        result = self.query(prompt, flow_metadata=flow_data)
        
        # Parse response into insights
        insights = self._parse_improvement_suggestions(result.response, flow_name)
        return insights
    
    # =========================================================================
    # CAPABILITY 7: Flow Validation
    # =========================================================================
    
    def validate_flow(self, flow_path: Union[str, Path]) -> List[FlowInsight]:
        """
        Validate a flow against best practices
        
        Args:
            flow_path: Path to flow or flow name
            
        Returns:
            List of validation findings
        """
        flow_data = self._load_flow(flow_path)
        analysis = self._parse_flow_metadata(flow_data)
        insights = []
        
        # Check for missing null handlers
        for decision in analysis.get('decisions', []):
            for rule in decision.get('rules', []):
                for condition in rule.get('conditions', []):
                    if condition.get('operator') == 'IsNull':
                        continue
                    # Check if there's a corresponding null check
                    has_null_check = any(
                        c.get('operator') == 'IsNull' and c.get('left') == condition.get('left')
                        for r in decision.get('rules', [])
                        for c in r.get('conditions', [])
                    )
                    if not has_null_check:
                        insights.append(FlowInsight(
                            category="Null Handling",
                            severity="warning",
                            message=f"No null check for {condition.get('left')} in decision {decision.get('name')}",
                            element=decision.get('name'),
                            recommendation="Add a null check before comparing values"
                        ))
        
        # Check for missing fault handlers on Apex
        for apex in analysis.get('apex_calls', []):
            insights.append(FlowInsight(
                category="Error Handling",
                severity="info",
                message=f"Apex callout '{apex.get('name')}' - ensure fault path is configured",
                element=apex.get('name'),
                recommendation="Add fault connector to handle Apex exceptions"
            ))
        
        # Check for hardcoded values
        for create in analysis.get('record_creates', []):
            for field_assign in create.get('fields', []):
                value = str(field_assign.get('value', ''))
                if not value.startswith('$') and not value.startswith('{'):
                    if value and value not in ['true', 'false', 'True', 'False']:
                        insights.append(FlowInsight(
                            category="Maintainability",
                            severity="info",
                            message=f"Hardcoded value '{value}' for field {field_assign.get('field')}",
                            element=create.get('name'),
                            recommendation="Consider using a variable or custom metadata for flexibility"
                        ))
        
        return insights
    
    # =========================================================================
    # CAPABILITY 8: Flow Comparison
    # =========================================================================
    
    def compare_flows(
        self,
        flow1_path: Union[str, Path],
        flow2_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Compare two flows and identify differences
        
        Args:
            flow1_path: Path to first flow
            flow2_path: Path to second flow
            
        Returns:
            Dictionary with differences
        """
        flow1 = self._load_flow(flow1_path)
        flow2 = self._load_flow(flow2_path)
        
        analysis1 = self.analyzer.analyze(flow1)
        analysis2 = self.analyzer.analyze(flow2)
        
        differences = {
            "flow1": self._extract_flow_name(flow1),
            "flow2": self._extract_flow_name(flow2),
            "structural_differences": [],
            "decision_differences": [],
            "trigger_differences": []
        }
        
        # Compare decisions
        decisions1 = {d['name']: d for d in analysis1.get('decisions', [])}
        decisions2 = {d['name']: d for d in analysis2.get('decisions', [])}
        
        for name in set(decisions1.keys()) | set(decisions2.keys()):
            if name not in decisions1:
                differences["decision_differences"].append(f"Added: {name}")
            elif name not in decisions2:
                differences["decision_differences"].append(f"Removed: {name}")
            elif decisions1[name] != decisions2[name]:
                differences["decision_differences"].append(f"Modified: {name}")
        
        # Compare triggers
        triggers1 = analysis1.get('trigger_conditions', [])
        triggers2 = analysis2.get('trigger_conditions', [])
        
        if triggers1 != triggers2:
            differences["trigger_differences"].append({
                "flow1_triggers": triggers1,
                "flow2_triggers": triggers2
            })
        
        return differences
    
    # =========================================================================
    # CAPABILITY 9: Impact Prediction
    # =========================================================================
    
    def predict_impact(
        self,
        flow_path: Union[str, Path],
        proposed_change: str
    ) -> Dict[str, Any]:
        """
        Predict the impact of a proposed change to a flow
        
        Args:
            flow_path: Path to flow
            proposed_change: Description of the proposed change
            
        Returns:
            Impact analysis
        """
        flow_data = self._load_flow(flow_path)
        flow_name = self._extract_flow_name(flow_data)
        
        prompt = f"""Analyze the impact of the following proposed change to the Salesforce Flow '{flow_name}':

PROPOSED CHANGE: {proposed_change}

Provide impact analysis including:
1. Affected components (decisions, record operations, etc.)
2. Potential risks
3. Testing recommendations
4. Rollback considerations
5. Downstream effects on other processes"""
        
        result = self.query(prompt, flow_metadata=flow_data)
        
        return {
            "flow": flow_name,
            "proposed_change": proposed_change,
            "impact_analysis": result.response,
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # CAPABILITY 10: Batch Operations
    # =========================================================================
    
    def batch_analyze(self, flow_paths: List[Union[str, Path]]) -> List[AnalysisResult]:
        """Analyze multiple flows"""
        return [self.analyze_flow(path) for path in flow_paths]
    
    def batch_validate(self, flow_paths: List[Union[str, Path]]) -> Dict[str, List[FlowInsight]]:
        """Validate multiple flows"""
        return {str(path): self.validate_flow(path) for path in flow_paths}
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _load_flow(self, flow_path: Union[str, Path]) -> Dict:
        """Load flow from file or cache"""
        path_str = str(flow_path)
        
        if path_str in self._flow_cache:
            return self._flow_cache[path_str]
        
        # Try as direct path
        if os.path.exists(path_str):
            with open(path_str) as f:
                flow_data = json.load(f)
        # Try in flows directory
        elif os.path.exists(self.flows_dir / f"{path_str}.json"):
            with open(self.flows_dir / f"{path_str}.json") as f:
                flow_data = json.load(f)
        else:
            raise FileNotFoundError(f"Flow not found: {path_str}")
        
        self._flow_cache[path_str] = flow_data
        return flow_data
    
    def _extract_flow_name(self, flow_data: Dict) -> str:
        """Extract flow name from metadata"""
        return (
            flow_data.get('MasterLabel') or
            flow_data.get('FullName') or
            flow_data.get('fullName') or
            flow_data.get('Metadata', {}).get('label') or
            flow_data.get('label') or
            'Unknown'
        )
    
    def _parse_flow_metadata(self, flow_data: Dict) -> Dict:
        """Parse flow metadata into analysis structure"""
        metadata = flow_data.get('Metadata', {})
        
        analysis = {
            'flow_name': self._extract_flow_name(flow_data),
            'developer_name': flow_data.get('FullName', ''),
            'process_type': flow_data.get('ProcessType', 'Unknown'),
            'trigger_type': None,
            'trigger_object': None,
            'trigger_conditions': [],
            'decisions': [],
            'record_lookups': [],
            'record_creates': [],
            'record_updates': [],
            'apex_calls': [],
            'screens': [],
        }
        
        # Extract trigger from start element
        start = metadata.get('start', {})
        if start:
            analysis['trigger_type'] = start.get('triggerType')
            analysis['trigger_object'] = start.get('object')
            
            for f in start.get('filters', []):
                value = f.get('value', {})
                if isinstance(value, dict):
                    value = value.get('stringValue') or value.get('booleanValue') or value.get('numberValue', '')
                analysis['trigger_conditions'].append({
                    'field': f.get('field'),
                    'operator': f.get('operator'),
                    'value': value
                })
        
        # Extract decisions
        for decision in metadata.get('decisions', []):
            dec_info = {'name': decision.get('name'), 'label': decision.get('label'), 'rules': []}
            for rule in decision.get('rules', []):
                rule_info = {'name': rule.get('name'), 'label': rule.get('label'), 'conditions': []}
                for cond in rule.get('conditions', []):
                    left = cond.get('leftValueReference', '')
                    right = cond.get('rightValue', {})
                    if isinstance(right, dict):
                        right = right.get('stringValue') or right.get('booleanValue') or right.get('numberValue', '')
                    rule_info['conditions'].append({
                        'left': left,
                        'operator': cond.get('operator', ''),
                        'right': right
                    })
                dec_info['rules'].append(rule_info)
            analysis['decisions'].append(dec_info)
        
        # Extract record lookups
        for lookup in metadata.get('recordLookups', []):
            analysis['record_lookups'].append({
                'name': lookup.get('name'),
                'label': lookup.get('label'),
                'object': lookup.get('object'),
            })
        
        # Extract record creates
        for create in metadata.get('recordCreates', []):
            analysis['record_creates'].append({
                'name': create.get('name'),
                'label': create.get('label'),
                'object': create.get('object'),
            })
        
        # Extract record updates
        for update in metadata.get('recordUpdates', []):
            analysis['record_updates'].append({
                'name': update.get('name'),
                'label': update.get('label'),
                'object': update.get('object') or update.get('inputReference', ''),
            })
        
        # Extract screens
        for screen in metadata.get('screens', []):
            analysis['screens'].append({
                'name': screen.get('name'),
                'label': screen.get('label'),
            })
        
        return analysis
    
    def _extract_record_ops(self, analysis: Dict) -> List[Dict]:
        """Extract all record operations"""
        ops = []
        ops.extend([{"type": "lookup", **op} for op in analysis.get('record_lookups', [])])
        ops.extend([{"type": "create", **op} for op in analysis.get('record_creates', [])])
        ops.extend([{"type": "update", **op} for op in analysis.get('record_updates', [])])
        return ops
    
    def _generate_insights(self, analysis: Dict) -> List[FlowInsight]:
        """Generate insights from analysis"""
        insights = []
        
        # Complexity insight
        decision_count = len(analysis.get('decisions', []))
        if decision_count > 5:
            insights.append(FlowInsight(
                category="Complexity",
                severity="warning",
                message=f"Flow has {decision_count} decisions - consider simplifying",
                recommendation="Break into subflows for maintainability"
            ))
        
        # Trigger insight
        triggers = analysis.get('trigger_conditions', [])
        if triggers:
            insights.append(FlowInsight(
                category="Trigger",
                severity="info",
                message=f"Flow has {len(triggers)} trigger conditions"
            ))
        
        return insights
    
    def _validate_response(
        self,
        response: str,
        expected: List[str]
    ) -> tuple[List[str], List[str]]:
        """Validate AI response against expected analysis"""
        response_lower = response.lower()
        matched = []
        missing = []
        
        for exp in expected:
            # Normalize for comparison
            exp_normalized = exp.lower().replace('_', ' ').replace('$', '').replace('{', '').replace('}', '')
            
            if exp_normalized in response_lower or exp.lower() in response_lower:
                matched.append(exp)
            else:
                # Check key parts
                key_parts = [p.strip() for p in exp_normalized.split() if len(p.strip()) > 3]
                if all(part in response_lower for part in key_parts[:3]):
                    matched.append(exp)
                else:
                    missing.append(exp)
        
        return matched, missing
    
    def _parse_improvement_suggestions(self, response: str, flow_name: str) -> List[FlowInsight]:
        """Parse AI response into FlowInsight objects"""
        insights = []
        
        # Simple parsing - in production, use structured output
        lines = response.split('\n')
        current_insight = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('- Category:'):
                if current_insight:
                    insights.append(FlowInsight(**current_insight))
                current_insight = {'category': line.replace('- Category:', '').strip()}
            elif line.startswith('- Severity:'):
                current_insight['severity'] = line.replace('- Severity:', '').strip().lower()
            elif line.startswith('- Issue:'):
                current_insight['message'] = line.replace('- Issue:', '').strip()
            elif line.startswith('- Recommendation:'):
                current_insight['recommendation'] = line.replace('- Recommendation:', '').strip()
        
        if current_insight and 'message' in current_insight:
            if 'severity' not in current_insight:
                current_insight['severity'] = 'info'
            if 'category' not in current_insight:
                current_insight['category'] = 'General'
            insights.append(FlowInsight(**current_insight))
        
        return insights
    
    def _generate_report_html(self, scenario_results: Optional[List[ScenarioResult]] = None) -> str:
        """Generate HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate statistics
        total = len(scenario_results) if scenario_results else 0
        passed = sum(1 for r in scenario_results if r.passed) if scenario_results else 0
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Flow AI Agent Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #0f172a; color: #f8fafc; }}
        .header {{ text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 2rem; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat {{ background: #1e293b; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #6366f1; }}
        .stat-label {{ color: #94a3b8; font-size: 0.9rem; }}
        .results {{ background: #1e293b; border-radius: 10px; padding: 20px; }}
        .result {{ padding: 15px; border-bottom: 1px solid #334155; }}
        .result:last-child {{ border-bottom: none; }}
        .passed {{ border-left: 4px solid #10b981; }}
        .failed {{ border-left: 4px solid #ef4444; }}
        .result-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
        .badge-pass {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
        .badge-fail {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}
        .query {{ color: #94a3b8; margin-top: 10px; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Flow AI Agent Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    <div class="stats">
        <div class="stat"><div class="stat-value">{total}</div><div class="stat-label">Total Tests</div></div>
        <div class="stat"><div class="stat-value" style="color: #10b981">{passed}</div><div class="stat-label">Passed</div></div>
        <div class="stat"><div class="stat-value" style="color: #ef4444">{failed}</div><div class="stat-label">Failed</div></div>
        <div class="stat"><div class="stat-value">{pass_rate:.1f}%</div><div class="stat-label">Pass Rate</div></div>
    </div>
    <div class="results">
        <h2>Test Results</h2>"""
        
        if scenario_results:
            for result in scenario_results:
                status_class = "passed" if result.passed else "failed"
                badge_class = "badge-pass" if result.passed else "badge-fail"
                badge_text = "PASSED" if result.passed else "FAILED"
                
                html += f"""
        <div class="result {status_class}">
            <div class="result-header">
                <strong>{result.scenario_id}</strong>
                <span class="badge {badge_class}">{badge_text}</span>
            </div>
            <div class="query">{result.query[:200]}...</div>
        </div>"""
        
        html += """
    </div>
</body>
</html>"""
        
        return html
    
    # =========================================================================
    # CLI Interface
    # =========================================================================
    
    @classmethod
    def cli(cls):
        """Command-line interface for the agent"""
        import argparse
        
        parser = argparse.ArgumentParser(
            description="Salesforce Flow AI Agent",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Analyze command
        analyze_parser = subparsers.add_parser("analyze", help="Analyze flows")
        analyze_parser.add_argument("--flow", help="Specific flow to analyze")
        analyze_parser.add_argument("--all", action="store_true", help="Analyze all flows")
        
        # Query command
        query_parser = subparsers.add_parser("query", help="Query flows with AI")
        query_parser.add_argument("question", help="Question to ask")
        query_parser.add_argument("--flow", help="Specific flow context")
        
        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate flows")
        validate_parser.add_argument("--flow", help="Specific flow to validate")
        
        # Test command
        test_parser = subparsers.add_parser("test", help="Run scenario tests")
        test_parser.add_argument("--limit", type=int, help="Limit scenarios")
        test_parser.add_argument("--category", help="Filter by category")
        test_parser.add_argument("--report", action="store_true", help="Generate report")
        
        # Regression command
        reg_parser = subparsers.add_parser("regression", help="Detect regressions")
        reg_parser.add_argument("--baseline", help="Baseline ID to compare")
        
        args = parser.parse_args()
        
        agent = cls(verbose=True)
        
        if args.command == "analyze":
            if args.all:
                results = agent.analyze_all_flows()
                for r in results:
                    print(f"{'✅' if r.success else '❌'} {r.flow_name}: {len(r.insights)} insights")
            elif args.flow:
                result = agent.analyze_flow(args.flow)
                print(result.to_json())
        
        elif args.command == "query":
            result = agent.query(args.question, flow_name=args.flow)
            print(result.response)
        
        elif args.command == "validate":
            insights = agent.validate_flow(args.flow)
            for i in insights:
                print(f"[{i.severity.upper()}] {i.category}: {i.message}")
        
        elif args.command == "test":
            results = agent.run_scenarios(
                limit=args.limit,
                category=args.category
            )
            passed = sum(1 for r in results if r.passed)
            print(f"\n{'='*50}")
            print(f"Results: {passed}/{len(results)} passed")
            
            if args.report:
                report_path = agent.generate_report(results)
                print(f"Report: {report_path}")
        
        elif args.command == "regression":
            changes = agent.detect_regression(args.baseline)
            print(json.dumps(changes, indent=2))
        
        else:
            parser.print_help()


# =========================================================================
# Convenience Functions
# =========================================================================

def create_agent(**kwargs) -> SalesforceFlowAgent:
    """Create a new agent instance"""
    return SalesforceFlowAgent(**kwargs)


def quick_query(question: str, flow_name: Optional[str] = None) -> str:
    """Quick query without explicit agent creation"""
    agent = SalesforceFlowAgent()
    result = agent.query(question, flow_name=flow_name)
    return result.response


def quick_analyze(flow_path: str) -> Dict:
    """Quick analysis without explicit agent creation"""
    agent = SalesforceFlowAgent()
    result = agent.analyze_flow(flow_path)
    return result.to_dict()


# =========================================================================
# Main Entry Point
# =========================================================================

if __name__ == "__main__":
    SalesforceFlowAgent.cli()

"""
Salesforce Metadata Analyzer with AI/LLM Integration
=====================================================
This module provides tools for analyzing Salesforce metadata (Flows, Apex, Objects)
using AI/LLM for intelligent insights, documentation, and recommendations.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum


class MetadataType(Enum):
    """Supported Salesforce metadata types"""
    FLOW = "Flow"
    APEX_CLASS = "ApexClass"
    APEX_TRIGGER = "ApexTrigger"
    CUSTOM_OBJECT = "CustomObject"
    CUSTOM_FIELD = "CustomField"
    VALIDATION_RULE = "ValidationRule"
    WORKFLOW_RULE = "WorkflowRule"
    PROCESS_BUILDER = "ProcessBuilder"


@dataclass
class FlowElement:
    """Represents a single element in a Flow"""
    name: str
    element_type: str
    label: Optional[str] = None
    description: Optional[str] = None
    connector: Optional[str] = None
    conditions: List[Dict] = field(default_factory=list)
    input_params: List[Dict] = field(default_factory=list)
    output_params: List[Dict] = field(default_factory=list)


@dataclass
class FlowAnalysis:
    """Complete analysis of a Salesforce Flow"""
    flow_name: str
    flow_label: str
    flow_type: str
    api_version: float
    status: str
    trigger_object: Optional[str] = None
    trigger_type: Optional[str] = None
    entry_conditions: List[Dict] = field(default_factory=list)
    elements: List[FlowElement] = field(default_factory=list)
    execution_paths: List[List[str]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SalesforceMetadataParser:
    """Parser for Salesforce metadata JSON files"""
    
    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self.raw_data: Dict = {}
        self.metadata_type: Optional[MetadataType] = None
        
    def load(self) -> Dict:
        """Load metadata from JSON file"""
        with open(self.metadata_path, 'r') as f:
            self.raw_data = json.load(f)
        self._detect_metadata_type()
        return self.raw_data
    
    def _detect_metadata_type(self):
        """Detect the type of Salesforce metadata"""
        attributes = self.raw_data.get('attributes', {})
        type_name = attributes.get('type', '')
        
        for mt in MetadataType:
            if mt.value.lower() == type_name.lower():
                self.metadata_type = mt
                return
        
        # Fallback detection based on structure
        if 'Metadata' in self.raw_data:
            metadata = self.raw_data['Metadata']
            if 'actionCalls' in metadata or 'decisions' in metadata:
                self.metadata_type = MetadataType.FLOW


class FlowAnalyzer:
    """
    Analyzes Salesforce Flow metadata and extracts insights
    """
    
    def __init__(self, flow_data: Dict):
        self.flow_data = flow_data
        self.metadata = flow_data.get('Metadata', {})
        self.analysis: Optional[FlowAnalysis] = None
        
    def analyze(self) -> FlowAnalysis:
        """Perform comprehensive flow analysis"""
        self.analysis = FlowAnalysis(
            flow_name=self._get_flow_name(),
            flow_label=self.metadata.get('label', 'Unknown'),
            flow_type=self.metadata.get('processType', 'Unknown'),
            api_version=self.metadata.get('apiVersion', 0),
            status=self.metadata.get('status', 'Unknown'),
        )
        
        self._analyze_trigger()
        self._analyze_elements()
        self._analyze_execution_paths()
        self._analyze_dependencies()
        self._check_best_practices()
        
        return self.analysis
    
    def _get_flow_name(self) -> str:
        """Extract flow name from interview label or label"""
        interview_label = self.metadata.get('interviewLabel', '')
        if interview_label:
            # Remove datetime placeholder
            return interview_label.replace(' {!$Flow.CurrentDateTime}', '').strip()
        return self.metadata.get('label', 'Unknown Flow')
    
    def _analyze_trigger(self):
        """Analyze flow trigger configuration"""
        start = self.metadata.get('start', {})
        
        if start:
            self.analysis.trigger_object = start.get('object')
            self.analysis.trigger_type = start.get('triggerType')
            
            # Extract entry conditions
            filters = start.get('filters', [])
            for f in filters:
                condition = {
                    'field': f.get('field'),
                    'operator': f.get('operator'),
                    'value': self._extract_value(f.get('value', {}))
                }
                self.analysis.entry_conditions.append(condition)
    
    def _analyze_elements(self):
        """Analyze all flow elements"""
        # Analyze Action Calls (Apex invocations, etc.)
        for action in self.metadata.get('actionCalls', []):
            element = FlowElement(
                name=action.get('name', ''),
                element_type='ActionCall',
                label=action.get('label'),
                description=action.get('description'),
                connector=self._get_connector_target(action.get('connector')),
                input_params=[{
                    'name': p.get('name'),
                    'value': self._extract_value(p.get('value', {}))
                } for p in action.get('inputParameters', [])]
            )
            self.analysis.elements.append(element)
        
        # Analyze Decisions
        for decision in self.metadata.get('decisions', []):
            rules = decision.get('rules', [])
            conditions = []
            
            for rule in rules:
                for cond in rule.get('conditions', []):
                    conditions.append({
                        'left': cond.get('leftValueReference'),
                        'operator': cond.get('operator'),
                        'right': self._extract_value(cond.get('rightValue', {})),
                        'requires_change': rule.get('doesRequireRecordChangedToMeetCriteria', False)
                    })
            
            element = FlowElement(
                name=decision.get('name', ''),
                element_type='Decision',
                label=decision.get('label'),
                description=decision.get('description'),
                conditions=conditions
            )
            self.analysis.elements.append(element)
        
        # Analyze Record Updates
        for update in self.metadata.get('recordUpdates', []):
            assignments = [{
                'field': a.get('field'),
                'value': self._extract_value(a.get('value', {}))
            } for a in update.get('inputAssignments', [])]
            
            element = FlowElement(
                name=update.get('name', ''),
                element_type='RecordUpdate',
                label=update.get('label'),
                description=update.get('description'),
                connector=self._get_connector_target(update.get('connector')),
                input_params=assignments
            )
            self.analysis.elements.append(element)
        
        # Analyze Loops
        for loop in self.metadata.get('loops', []):
            element = FlowElement(
                name=loop.get('name', ''),
                element_type='Loop',
                label=loop.get('label'),
                description=loop.get('description')
            )
            self.analysis.elements.append(element)
        
        # Analyze Subflows
        for subflow in self.metadata.get('subflows', []):
            element = FlowElement(
                name=subflow.get('name', ''),
                element_type='Subflow',
                label=subflow.get('label'),
                description=subflow.get('description')
            )
            self.analysis.elements.append(element)
    
    def _analyze_execution_paths(self):
        """Trace all possible execution paths through the flow"""
        start = self.metadata.get('start', {})
        
        # Get immediate execution path
        if start.get('connector'):
            path = ['Start']
            target = self._get_connector_target(start.get('connector'))
            self._trace_path(target, path.copy())
        
        # Get scheduled paths
        for scheduled in start.get('scheduledPaths', []):
            path = [f"Scheduled: {scheduled.get('label', 'Unknown')}"]
            target = self._get_connector_target(scheduled.get('connector'))
            self._trace_path(target, path.copy())
    
    def _trace_path(self, element_name: str, current_path: List[str], visited: set = None):
        """Recursively trace execution path"""
        if visited is None:
            visited = set()
        
        if not element_name or element_name in visited:
            self.analysis.execution_paths.append(current_path)
            return
        
        visited.add(element_name)
        current_path.append(element_name)
        
        # Find the element and its connectors
        element = self._find_element(element_name)
        if not element:
            self.analysis.execution_paths.append(current_path)
            return
        
        # Get next connectors based on element type
        connectors = self._get_element_connectors(element)
        
        if not connectors:
            self.analysis.execution_paths.append(current_path)
        else:
            for connector in connectors:
                self._trace_path(connector, current_path.copy(), visited.copy())
    
    def _find_element(self, name: str) -> Optional[Dict]:
        """Find an element by name in all element collections"""
        collections = ['actionCalls', 'decisions', 'recordUpdates', 'loops', 
                      'assignments', 'recordCreates', 'recordLookups', 'screens']
        
        for collection in collections:
            for element in self.metadata.get(collection, []):
                if element.get('name') == name:
                    return element
        return None
    
    def _get_element_connectors(self, element: Dict) -> List[str]:
        """Get all possible next elements from an element"""
        connectors = []
        
        # Direct connector
        if element.get('connector'):
            target = self._get_connector_target(element['connector'])
            if target:
                connectors.append(target)
        
        # Decision rules connectors
        for rule in element.get('rules', []):
            if rule.get('connector'):
                target = self._get_connector_target(rule['connector'])
                if target:
                    connectors.append(target)
        
        # Default connector for decisions
        if element.get('defaultConnector'):
            target = self._get_connector_target(element['defaultConnector'])
            if target:
                connectors.append(target)
        
        return connectors
    
    def _analyze_dependencies(self):
        """Extract all dependencies (objects, fields, Apex classes)"""
        dependencies = {
            'objects': set(),
            'fields': set(),
            'apex_classes': set(),
            'flows': set()
        }
        
        # Object from trigger
        if self.analysis.trigger_object:
            dependencies['objects'].add(self.analysis.trigger_object)
        
        # Fields from conditions and assignments
        self._extract_field_references(self.metadata, dependencies)
        
        # Apex classes from action calls
        for action in self.metadata.get('actionCalls', []):
            if action.get('actionType') == 'apex':
                apex_class = action.get('actionName') or action.get('nameSegment')
                if apex_class:
                    dependencies['apex_classes'].add(apex_class)
        
        # Subflows
        for subflow in self.metadata.get('subflows', []):
            flow_name = subflow.get('flowName')
            if flow_name:
                dependencies['flows'].add(flow_name)
        
        # Convert sets to lists
        self.analysis.dependencies = {k: list(v) for k, v in dependencies.items()}
    
    def _extract_field_references(self, data: Any, dependencies: Dict):
        """Recursively extract field references from metadata"""
        if isinstance(data, dict):
            # Check for field references
            if 'leftValueReference' in data:
                ref = data['leftValueReference']
                if ref and '.' in ref:
                    parts = ref.replace('$Record.', '').split('.')
                    if parts:
                        dependencies['fields'].add(parts[0])
            
            if 'elementReference' in data:
                ref = data.get('elementReference')
                if ref and '$Record.' in str(ref):
                    field_name = ref.replace('$Record.', '')
                    dependencies['fields'].add(field_name)
            
            if 'field' in data:
                dependencies['fields'].add(data['field'])
            
            # Recurse
            for value in data.values():
                self._extract_field_references(value, dependencies)
                
        elif isinstance(data, list):
            for item in data:
                self._extract_field_references(item, dependencies)
    
    def _check_best_practices(self):
        """Check for best practices and potential issues"""
        # Check for DML in loops
        loops = self.metadata.get('loops', [])
        record_ops = (
            self.metadata.get('recordUpdates', []) +
            self.metadata.get('recordCreates', []) +
            self.metadata.get('recordDeletes', [])
        )
        
        if loops and record_ops:
            # Simplified check - in reality would need path analysis
            self.analysis.issues.append(
                "⚠️ Potential DML operations detected. Ensure DML is not inside loops to avoid governor limits."
            )
        
        # Check for missing fault paths
        for action in self.metadata.get('actionCalls', []):
            if not action.get('faultConnector'):
                self.analysis.issues.append(
                    f"⚠️ Action '{action.get('label', action.get('name'))}' has no fault connector for error handling."
                )
        
        # Check for hardcoded values
        hardcoded_count = self._count_hardcoded_values(self.metadata)
        if hardcoded_count > 5:
            self.analysis.recommendations.append(
                f"💡 Found {hardcoded_count} hardcoded values. Consider using Custom Metadata or Custom Labels for configurability."
            )
        
        # Check API version
        if self.analysis.api_version < 58:
            self.analysis.recommendations.append(
                f"💡 Flow is using API version {self.analysis.api_version}. Consider upgrading to latest API version for new features."
            )
        
        # Check for scheduled paths timing
        start = self.metadata.get('start', {})
        for scheduled in start.get('scheduledPaths', []):
            offset = scheduled.get('offsetNumber', 0)
            unit = scheduled.get('offsetUnit', '')
            if offset > 0:
                self.analysis.recommendations.append(
                    f"📅 Scheduled path '{scheduled.get('label')}' runs {offset} {unit} after trigger. Verify this timing meets business requirements."
                )
    
    def _count_hardcoded_values(self, data: Any, count: int = 0) -> int:
        """Count hardcoded string values in metadata"""
        if isinstance(data, dict):
            if 'stringValue' in data and data['stringValue']:
                count += 1
            for value in data.values():
                count = self._count_hardcoded_values(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_hardcoded_values(item, count)
        return count
    
    def _extract_value(self, value_dict: Dict) -> Any:
        """Extract the actual value from a Salesforce value object"""
        if not value_dict:
            return None
        
        value_fields = ['stringValue', 'numberValue', 'booleanValue', 
                       'dateValue', 'dateTimeValue', 'elementReference']
        
        for field in value_fields:
            if value_dict.get(field) is not None:
                return value_dict[field]
        return None
    
    def _get_connector_target(self, connector: Optional[Dict]) -> Optional[str]:
        """Extract target reference from a connector"""
        if connector and isinstance(connector, dict):
            return connector.get('targetReference')
        return None


class AIMetadataInsights:
    """
    Generate AI-powered insights and documentation from metadata analysis
    """
    
    def __init__(self, analysis: FlowAnalysis):
        self.analysis = analysis
    
    def generate_summary(self) -> str:
        """Generate a human-readable summary of the flow"""
        summary = []
        summary.append(f"# Flow Analysis: {self.analysis.flow_label}")
        summary.append("")
        summary.append("## Overview")
        summary.append(f"- **Type:** {self.analysis.flow_type}")
        summary.append(f"- **Status:** {self.analysis.status}")
        summary.append(f"- **API Version:** {self.analysis.api_version}")
        
        if self.analysis.trigger_object:
            summary.append(f"- **Trigger Object:** {self.analysis.trigger_object}")
            summary.append(f"- **Trigger Type:** {self.analysis.trigger_type}")
        
        summary.append("")
        summary.append("## Entry Conditions")
        if self.analysis.entry_conditions:
            for cond in self.analysis.entry_conditions:
                summary.append(f"- `{cond['field']}` {cond['operator']} `{cond['value']}`")
        else:
            summary.append("- No entry conditions (runs on all records)")
        
        summary.append("")
        summary.append("## Flow Elements")
        element_types = {}
        for element in self.analysis.elements:
            et = element.element_type
            if et not in element_types:
                element_types[et] = []
            element_types[et].append(element)
        
        for et, elements in element_types.items():
            summary.append(f"\n### {et}s ({len(elements)})")
            for elem in elements:
                summary.append(f"- **{elem.label or elem.name}**")
                if elem.description:
                    summary.append(f"  - {elem.description}")
                if elem.conditions:
                    for cond in elem.conditions:
                        summary.append(f"  - Condition: `{cond['left']}` {cond['operator']} `{cond['right']}`")
        
        summary.append("")
        summary.append("## Execution Paths")
        for i, path in enumerate(self.analysis.execution_paths, 1):
            summary.append(f"\n### Path {i}")
            summary.append(" → ".join(path))
        
        summary.append("")
        summary.append("## Dependencies")
        deps = self.analysis.dependencies
        if deps.get('objects'):
            summary.append(f"- **Objects:** {', '.join(deps['objects'])}")
        if deps.get('fields'):
            summary.append(f"- **Fields:** {', '.join(deps['fields'])}")
        if deps.get('apex_classes'):
            summary.append(f"- **Apex Classes:** {', '.join(deps['apex_classes'])}")
        if deps.get('flows'):
            summary.append(f"- **Referenced Flows:** {', '.join(deps['flows'])}")
        
        if self.analysis.issues:
            summary.append("")
            summary.append("## ⚠️ Issues Found")
            for issue in self.analysis.issues:
                summary.append(f"- {issue}")
        
        if self.analysis.recommendations:
            summary.append("")
            summary.append("## 💡 Recommendations")
            for rec in self.analysis.recommendations:
                summary.append(f"- {rec}")
        
        return "\n".join(summary)
    
    def generate_business_description(self) -> str:
        """Generate business-friendly description of what the flow does"""
        desc = []
        desc.append(f"## Business Process: {self.analysis.flow_label}")
        desc.append("")
        
        # Describe trigger
        if self.analysis.trigger_object and self.analysis.trigger_type:
            trigger_desc = self._describe_trigger()
            desc.append(f"**When it runs:** {trigger_desc}")
            desc.append("")
        
        # Describe conditions
        if self.analysis.entry_conditions:
            desc.append("**Conditions:**")
            for cond in self.analysis.entry_conditions:
                desc.append(f"- The {cond['field']} must be {self._humanize_operator(cond['operator'])} '{cond['value']}'")
            desc.append("")
        
        # Describe actions
        desc.append("**What it does:**")
        for element in self.analysis.elements:
            action_desc = self._describe_element(element)
            if action_desc:
                desc.append(f"- {action_desc}")
        
        return "\n".join(desc)
    
    def _describe_trigger(self) -> str:
        """Create human-readable trigger description"""
        obj = self.analysis.trigger_object
        trigger_type = self.analysis.trigger_type
        
        trigger_map = {
            'RecordAfterSave': f'After a {obj} record is created or updated',
            'RecordBeforeSave': f'Before a {obj} record is saved',
            'RecordBeforeDelete': f'Before a {obj} record is deleted',
            'Scheduled': 'On a scheduled basis',
            'PlatformEvent': 'When a platform event is received'
        }
        
        return trigger_map.get(trigger_type, f'When triggered on {obj}')
    
    def _describe_element(self, element: FlowElement) -> str:
        """Create human-readable element description"""
        if element.element_type == 'Decision':
            conditions = element.conditions
            if conditions:
                cond = conditions[0]
                return f"Checks if {cond['left']} {self._humanize_operator(cond['operator'])} '{cond['right']}'"
        
        elif element.element_type == 'RecordUpdate':
            if element.input_params:
                updates = [f"{p['field']} to '{p['value']}'" for p in element.input_params]
                return f"Updates the record: sets {', '.join(updates)}"
        
        elif element.element_type == 'ActionCall':
            return f"Calls the '{element.label or element.name}' action"
        
        return None
    
    def _humanize_operator(self, operator: str) -> str:
        """Convert operator to human-readable form"""
        operators = {
            'EqualTo': 'equal to',
            'NotEqualTo': 'not equal to',
            'GreaterThan': 'greater than',
            'LessThan': 'less than',
            'Contains': 'contains',
            'StartsWith': 'starts with',
            'IsNull': 'is empty'
        }
        return operators.get(operator, operator)
    
    def generate_llm_prompt(self) -> str:
        """Generate a prompt for LLM to analyze the flow"""
        prompt = f"""Analyze this Salesforce Flow and provide insights:

## Flow Information
- Name: {self.analysis.flow_label}
- Type: {self.analysis.flow_type}
- Trigger Object: {self.analysis.trigger_object}
- Trigger Type: {self.analysis.trigger_type}

## Entry Conditions
{json.dumps(self.analysis.entry_conditions, indent=2)}

## Elements
{json.dumps([{'name': e.name, 'type': e.element_type, 'label': e.label, 'conditions': e.conditions} for e in self.analysis.elements], indent=2)}

## Execution Paths
{json.dumps(self.analysis.execution_paths, indent=2)}

## Dependencies
{json.dumps(self.analysis.dependencies, indent=2)}

Please provide:
1. A business-friendly explanation of what this flow does
2. Potential risks or issues
3. Optimization recommendations
4. Security considerations
5. Testing recommendations
"""
        return prompt


def analyze_flow_file(file_path: str) -> tuple[FlowAnalysis, str, str]:
    """
    Main function to analyze a Flow metadata file
    
    Args:
        file_path: Path to the Flow JSON file
        
    Returns:
        Tuple of (FlowAnalysis, summary_markdown, business_description)
    """
    # Parse the metadata
    parser = SalesforceMetadataParser(file_path)
    data = parser.load()
    
    # Analyze the flow
    analyzer = FlowAnalyzer(data)
    analysis = analyzer.analyze()
    
    # Generate insights
    insights = AIMetadataInsights(analysis)
    summary = insights.generate_summary()
    business_desc = insights.generate_business_description()
    
    return analysis, summary, business_desc


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python salesforce_metadata_analyzer.py <flow_json_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    analysis, summary, business_desc = analyze_flow_file(file_path)
    
    print(summary)
    print("\n" + "="*80 + "\n")
    print(business_desc)

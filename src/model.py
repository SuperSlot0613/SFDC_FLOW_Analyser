"""
Salesforce Metadata AI Model
=============================
A unified AI model that can perform comprehensive Salesforce metadata analysis,
including Flow analysis, dependency mapping, impact analysis, documentation generation,
code review, and intelligent recommendations.

This model can work standalone (rule-based) or enhanced with LLM capabilities.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib
from datetime import datetime


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class TaskType(Enum):
    """Types of analysis tasks the model can perform"""
    FLOW_ANALYSIS = "flow_analysis"
    APEX_ANALYSIS = "apex_analysis"
    DEPENDENCY_MAPPING = "dependency_mapping"
    IMPACT_ANALYSIS = "impact_analysis"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    SECURITY_REVIEW = "security_review"
    OPTIMIZATION = "optimization"
    MIGRATION_ANALYSIS = "migration_analysis"
    CUSTOM_QUERY = "custom_query"


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
    PERMISSION_SET = "PermissionSet"
    PROFILE = "Profile"
    LIGHTNING_COMPONENT = "LightningComponent"


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Issue:
    """Represents an identified issue"""
    severity: Severity
    category: str
    message: str
    location: Optional[str] = None
    recommendation: Optional[str] = None
    code: Optional[str] = None


@dataclass
class Dependency:
    """Represents a dependency relationship"""
    source_type: str
    source_name: str
    target_type: str
    target_name: str
    relationship: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Unified result structure for all analysis tasks"""
    task_type: TaskType
    metadata_type: MetadataType
    metadata_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    
    # Analysis outputs
    summary: str = ""
    details: Dict = field(default_factory=dict)
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    
    # For documentation tasks
    documentation: str = ""
    
    # For custom queries
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "task_type": self.task_type.value,
            "metadata_type": self.metadata_type.value,
            "metadata_name": self.metadata_name,
            "timestamp": self.timestamp,
            "success": self.success,
            "summary": self.summary,
            "details": self.details,
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "location": i.location,
                    "recommendation": i.recommendation
                }
                for i in self.issues
            ],
            "recommendations": self.recommendations,
            "dependencies": [
                {
                    "source": f"{d.source_type}:{d.source_name}",
                    "target": f"{d.target_type}:{d.target_name}",
                    "relationship": d.relationship
                }
                for d in self.dependencies
            ],
            "metrics": self.metrics,
            "documentation": self.documentation
        }
    
    def to_markdown(self) -> str:
        """Convert to Markdown format"""
        md = []
        md.append(f"# {self.task_type.value.replace('_', ' ').title()}: {self.metadata_name}")
        md.append(f"\n**Type:** {self.metadata_type.value}")
        md.append(f"**Timestamp:** {self.timestamp}")
        
        if self.summary:
            md.append(f"\n## Summary\n{self.summary}")
        
        if self.issues:
            md.append("\n## Issues Found")
            for issue in sorted(self.issues, key=lambda x: x.severity.value):
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "ℹ️"}
                md.append(f"\n### {icon.get(issue.severity.value, '•')} [{issue.severity.value.upper()}] {issue.category}")
                md.append(f"{issue.message}")
                if issue.recommendation:
                    md.append(f"\n**Recommendation:** {issue.recommendation}")
        
        if self.recommendations:
            md.append("\n## Recommendations")
            for rec in self.recommendations:
                md.append(f"- {rec}")
        
        if self.dependencies:
            md.append("\n## Dependencies")
            for dep in self.dependencies:
                md.append(f"- {dep.source_name} --[{dep.relationship}]--> {dep.target_name}")
        
        if self.metrics:
            md.append("\n## Metrics")
            for key, value in self.metrics.items():
                md.append(f"- **{key}:** {value}")
        
        if self.documentation:
            md.append(f"\n## Documentation\n{self.documentation}")
        
        return "\n".join(md)


# =============================================================================
# ANALYSIS ENGINES (Rule-Based)
# =============================================================================

class BaseAnalysisEngine(ABC):
    """Abstract base class for analysis engines"""
    
    @abstractmethod
    def analyze(self, metadata: Dict, options: Dict = None) -> AnalysisResult:
        """Perform analysis on metadata"""
        pass
    
    @abstractmethod
    def get_supported_tasks(self) -> List[TaskType]:
        """Return list of supported task types"""
        pass


class FlowAnalysisEngine(BaseAnalysisEngine):
    """
    Engine for analyzing Salesforce Flow metadata
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[Callable]:
        """Initialize analysis rules"""
        return [
            self._check_fault_handlers,
            self._check_dml_in_loops,
            self._check_hardcoded_values,
            self._check_api_version,
            self._check_naming_conventions,
            self._check_documentation,
            self._check_bulkification,
            self._check_security,
        ]
    
    def get_supported_tasks(self) -> List[TaskType]:
        return [
            TaskType.FLOW_ANALYSIS,
            TaskType.CODE_REVIEW,
            TaskType.SECURITY_REVIEW,
            TaskType.OPTIMIZATION,
            TaskType.DOCUMENTATION,
            TaskType.DEPENDENCY_MAPPING
        ]
    
    def analyze(self, metadata: Dict, options: Dict = None) -> AnalysisResult:
        """Perform comprehensive flow analysis"""
        options = options or {}
        flow_metadata = metadata.get('Metadata', metadata)
        
        result = AnalysisResult(
            task_type=options.get('task_type', TaskType.FLOW_ANALYSIS),
            metadata_type=MetadataType.FLOW,
            metadata_name=self._get_flow_name(flow_metadata)
        )
        
        # Extract basic info
        result.details = self._extract_flow_details(flow_metadata)
        result.summary = self._generate_summary(flow_metadata, result.details)
        
        # Run all rules
        for rule in self.rules:
            issues = rule(flow_metadata)
            result.issues.extend(issues)
        
        # Extract dependencies
        result.dependencies = self._extract_dependencies(flow_metadata, result.metadata_name)
        
        # Calculate metrics
        result.metrics = self._calculate_metrics(flow_metadata, result)
        
        # Generate recommendations based on issues
        result.recommendations = self._generate_recommendations(result.issues)
        
        # Generate documentation if requested
        if options.get('generate_docs', True):
            result.documentation = self._generate_documentation(flow_metadata, result)
        
        return result
    
    def _get_flow_name(self, metadata: Dict) -> str:
        """Extract flow name"""
        interview = metadata.get('interviewLabel', '')
        if interview:
            return interview.replace(' {!$Flow.CurrentDateTime}', '').strip()
        return metadata.get('label', 'Unknown Flow')
    
    def _extract_flow_details(self, metadata: Dict) -> Dict:
        """Extract detailed flow information"""
        start = metadata.get('start') or {}
        
        return {
            "type": metadata.get('processType', 'Unknown'),
            "status": metadata.get('status', 'Unknown'),
            "api_version": metadata.get('apiVersion', 0),
            "trigger_object": start.get('object') if start else None,
            "trigger_type": start.get('triggerType') if start else None,
            "record_trigger_type": start.get('recordTriggerType') if start else None,
            "elements": {
                "decisions": len(metadata.get('decisions', [])),
                "actions": len(metadata.get('actionCalls', [])),
                "loops": len(metadata.get('loops', [])),
                "assignments": len(metadata.get('assignments', [])),
                "record_creates": len(metadata.get('recordCreates', [])),
                "record_updates": len(metadata.get('recordUpdates', [])),
                "record_deletes": len(metadata.get('recordDeletes', [])),
                "record_lookups": len(metadata.get('recordLookups', [])),
                "screens": len(metadata.get('screens', [])),
                "subflows": len(metadata.get('subflows', [])),
            },
            "has_scheduled_paths": bool(start.get('scheduledPaths')) if start else False,
            "entry_conditions": self._extract_entry_conditions(metadata)
        }
    
    def _extract_entry_conditions(self, metadata: Dict) -> List[Dict]:
        """Extract entry conditions"""
        start = metadata.get('start') or {}
        conditions = []
        
        for f in start.get('filters', []):
            conditions.append({
                "field": f.get('field'),
                "operator": f.get('operator'),
                "value": self._extract_value(f.get('value', {}))
            })
        
        return conditions
    
    def _extract_value(self, value_dict: Dict) -> Any:
        """Extract actual value from Salesforce value object"""
        for key in ['stringValue', 'numberValue', 'booleanValue', 'dateValue', 'elementReference']:
            if value_dict.get(key) is not None:
                return value_dict[key]
        return None
    
    def _generate_summary(self, metadata: Dict, details: Dict) -> str:
        """Generate human-readable summary"""
        flow_type = details['type']
        trigger = details.get('trigger_object', 'N/A')
        
        total_elements = sum(details['elements'].values())
        
        summary = f"This is a {flow_type} "
        
        if trigger and trigger != 'N/A':
            summary += f"triggered on {trigger} ({details.get('trigger_type', 'Unknown')} trigger). "
        
        summary += f"It contains {total_elements} elements including "
        
        element_summary = []
        for elem_type, count in details['elements'].items():
            if count > 0:
                element_summary.append(f"{count} {elem_type.replace('_', ' ')}")
        
        summary += ", ".join(element_summary[:5])
        if len(element_summary) > 5:
            summary += f", and {len(element_summary) - 5} more element types"
        
        summary += "."
        
        return summary
    
    # Rule implementations
    def _check_fault_handlers(self, metadata: Dict) -> List[Issue]:
        """Check for missing fault handlers"""
        issues = []
        
        for action in metadata.get('actionCalls', []):
            if not action.get('faultConnector'):
                issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Error Handling",
                    message=f"Action '{action.get('label', action.get('name'))}' has no fault connector",
                    location=f"actionCalls/{action.get('name')}",
                    recommendation="Add a fault connector to handle errors gracefully"
                ))
        
        for subflow in metadata.get('subflows', []):
            if not subflow.get('faultConnector'):
                issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Error Handling",
                    message=f"Subflow '{subflow.get('label', subflow.get('name'))}' has no fault connector",
                    location=f"subflows/{subflow.get('name')}",
                    recommendation="Add fault handling for subflow failures"
                ))
        
        return issues
    
    def _check_dml_in_loops(self, metadata: Dict) -> List[Issue]:
        """Check for DML operations potentially in loops"""
        issues = []
        
        loops = metadata.get('loops', [])
        dml_ops = (
            metadata.get('recordCreates', []) +
            metadata.get('recordUpdates', []) +
            metadata.get('recordDeletes', [])
        )
        
        if loops and dml_ops:
            # Simplified check - would need path analysis for accuracy
            issues.append(Issue(
                severity=Severity.HIGH,
                category="Governor Limits",
                message="Flow contains both loops and DML operations. Ensure DML is not inside loops.",
                recommendation="Move DML operations outside of loops or use collection variables to bulkify"
            ))
        
        return issues
    
    def _check_hardcoded_values(self, metadata: Dict) -> List[Issue]:
        """Check for excessive hardcoded values"""
        issues = []
        
        hardcoded_count = self._count_hardcoded_values(metadata)
        
        if hardcoded_count > 10:
            issues.append(Issue(
                severity=Severity.MEDIUM,
                category="Maintainability",
                message=f"Found {hardcoded_count} hardcoded values in the flow",
                recommendation="Consider using Custom Metadata Types or Custom Labels for configurable values"
            ))
        elif hardcoded_count > 5:
            issues.append(Issue(
                severity=Severity.LOW,
                category="Maintainability",
                message=f"Found {hardcoded_count} hardcoded values in the flow",
                recommendation="Review hardcoded values and externalize where appropriate"
            ))
        
        return issues
    
    def _count_hardcoded_values(self, data: Any, count: int = 0) -> int:
        """Recursively count hardcoded string values"""
        if isinstance(data, dict):
            if 'stringValue' in data and data['stringValue']:
                count += 1
            for value in data.values():
                count = self._count_hardcoded_values(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_hardcoded_values(item, count)
        return count
    
    def _check_api_version(self, metadata: Dict) -> List[Issue]:
        """Check API version"""
        issues = []
        api_version = metadata.get('apiVersion', 0)
        
        # Convert to float for comparison (API versions like "59.0")
        try:
            api_version = float(api_version) if api_version else 0
        except (ValueError, TypeError):
            api_version = 0
        
        if api_version < 50:
            issues.append(Issue(
                severity=Severity.MEDIUM,
                category="Compatibility",
                message=f"Flow uses outdated API version {api_version}",
                recommendation="Upgrade to latest API version for new features and bug fixes"
            ))
        elif api_version < 58:
            issues.append(Issue(
                severity=Severity.LOW,
                category="Compatibility",
                message=f"Flow uses API version {api_version}. Consider upgrading.",
                recommendation="Newer API versions include performance improvements and additional features"
            ))
        
        return issues
    
    def _check_naming_conventions(self, metadata: Dict) -> List[Issue]:
        """Check naming conventions"""
        issues = []
        
        # Check element names
        all_elements = []
        for key in ['decisions', 'actionCalls', 'assignments', 'loops', 'recordCreates', 
                    'recordUpdates', 'recordDeletes', 'recordLookups', 'screens', 'variables']:
            all_elements.extend(metadata.get(key, []))
        
        for elem in all_elements:
            name = elem.get('name', '')
            if name and not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
                issues.append(Issue(
                    severity=Severity.INFO,
                    category="Naming Convention",
                    message=f"Element name '{name}' may not follow best practices",
                    recommendation="Use descriptive PascalCase or camelCase names"
                ))
        
        return issues
    
    def _check_documentation(self, metadata: Dict) -> List[Issue]:
        """Check for missing documentation"""
        issues = []
        
        # Check flow description
        if not metadata.get('description'):
            issues.append(Issue(
                severity=Severity.LOW,
                category="Documentation",
                message="Flow has no description",
                recommendation="Add a description explaining the flow's purpose"
            ))
        
        # Check element descriptions
        undocumented = 0
        for key in ['decisions', 'actionCalls', 'screens']:
            for elem in metadata.get(key, []):
                if not elem.get('description'):
                    undocumented += 1
        
        if undocumented > 5:
            issues.append(Issue(
                severity=Severity.INFO,
                category="Documentation",
                message=f"{undocumented} key elements lack descriptions",
                recommendation="Add descriptions to improve maintainability"
            ))
        
        return issues
    
    def _check_bulkification(self, metadata: Dict) -> List[Issue]:
        """Check bulkification patterns"""
        issues = []
        
        # Check if flow handles collections
        has_collection_vars = any(
            v.get('isCollection') for v in metadata.get('variables', [])
        )
        
        # Check for record lookups without limits
        for lookup in metadata.get('recordLookups', []):
            if not lookup.get('limit') and lookup.get('getFirstRecordOnly') != True:
                issues.append(Issue(
                    severity=Severity.LOW,
                    category="Performance",
                    message=f"Record lookup '{lookup.get('label', lookup.get('name'))}' has no record limit",
                    recommendation="Consider adding a limit or using getFirstRecordOnly for single record lookups"
                ))
        
        return issues
    
    def _check_security(self, metadata: Dict) -> List[Issue]:
        """Check security considerations"""
        issues = []
        
        # Check run mode
        run_mode = metadata.get('runInMode')
        if run_mode == 'SystemModeWithoutSharing':
            issues.append(Issue(
                severity=Severity.HIGH,
                category="Security",
                message="Flow runs in System Mode without sharing rules",
                recommendation="Review if this is intentional and necessary. Consider using System Mode with sharing."
            ))
        
        # Check for sensitive field access (basic check)
        sensitive_patterns = ['password', 'ssn', 'credit', 'secret', 'token']
        metadata_str = json.dumps(metadata).lower()
        
        for pattern in sensitive_patterns:
            if pattern in metadata_str:
                issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Security",
                    message=f"Flow may access sensitive data (detected pattern: '{pattern}')",
                    recommendation="Ensure proper field-level security and audit logging"
                ))
                break
        
        return issues
    
    def _extract_dependencies(self, metadata: Dict, flow_name: str) -> List[Dependency]:
        """Extract all dependencies"""
        deps = []
        
        # Object dependencies
        start = metadata.get('start') or {}
        if start and start.get('object'):
            deps.append(Dependency(
                source_type="Flow",
                source_name=flow_name,
                target_type="Object",
                target_name=start['object'],
                relationship="triggers_on"
            ))
        
        # Apex dependencies
        for action in metadata.get('actionCalls', []):
            if action.get('actionType') == 'apex':
                class_name = action.get('actionName') or action.get('nameSegment')
                if class_name:
                    deps.append(Dependency(
                        source_type="Flow",
                        source_name=flow_name,
                        target_type="ApexClass",
                        target_name=class_name,
                        relationship="invokes"
                    ))
        
        # Subflow dependencies
        for subflow in metadata.get('subflows', []):
            if subflow.get('flowName'):
                deps.append(Dependency(
                    source_type="Flow",
                    source_name=flow_name,
                    target_type="Flow",
                    target_name=subflow['flowName'],
                    relationship="calls"
                ))
        
        # Field dependencies
        fields = self._extract_field_references(metadata)
        trigger_obj = start.get('object', 'Unknown') if start else 'Unknown'
        
        for field_name, access_type in fields:
            deps.append(Dependency(
                source_type="Flow",
                source_name=flow_name,
                target_type="Field",
                target_name=f"{trigger_obj}.{field_name}",
                relationship=access_type
            ))
        
        return deps
    
    def _extract_field_references(self, data: Any, fields: set = None) -> set:
        """Recursively extract field references"""
        if fields is None:
            fields = set()
        
        if isinstance(data, dict):
            # Check various reference patterns
            for key in ['leftValueReference', 'elementReference']:
                ref = data.get(key)
                if ref and isinstance(ref, str) and '$Record.' in ref:
                    field_name = ref.replace('$Record.', '').split('.')[0]
                    fields.add((field_name, 'reads'))
            
            if 'field' in data and data.get('field'):
                fields.add((data['field'], 'writes'))
            
            for value in data.values():
                self._extract_field_references(value, fields)
        
        elif isinstance(data, list):
            for item in data:
                self._extract_field_references(item, fields)
        
        return fields
    
    def _calculate_metrics(self, metadata: Dict, result: AnalysisResult) -> Dict:
        """Calculate analysis metrics"""
        details = result.details
        
        return {
            "total_elements": sum(details.get('elements', {}).values()),
            "complexity_score": self._calculate_complexity(metadata),
            "issue_count": len(result.issues),
            "critical_issues": len([i for i in result.issues if i.severity == Severity.CRITICAL]),
            "high_issues": len([i for i in result.issues if i.severity == Severity.HIGH]),
            "dependency_count": len(result.dependencies),
            "maintainability_score": self._calculate_maintainability(metadata, result)
        }
    
    def _calculate_complexity(self, metadata: Dict) -> int:
        """Calculate flow complexity score"""
        score = 0
        
        # Base complexity from element counts
        score += len(metadata.get('decisions', [])) * 3
        score += len(metadata.get('loops', [])) * 5
        score += len(metadata.get('actionCalls', [])) * 2
        score += len(metadata.get('subflows', [])) * 4
        score += len(metadata.get('screens', [])) * 2
        
        # Add complexity for nested conditions
        for decision in metadata.get('decisions', []):
            for rule in decision.get('rules', []):
                score += len(rule.get('conditions', []))
        
        return score
    
    def _calculate_maintainability(self, metadata: Dict, result: AnalysisResult) -> str:
        """Calculate maintainability rating"""
        score = 100
        
        # Deduct for issues
        for issue in result.issues:
            if issue.severity == Severity.CRITICAL:
                score -= 20
            elif issue.severity == Severity.HIGH:
                score -= 10
            elif issue.severity == Severity.MEDIUM:
                score -= 5
            elif issue.severity == Severity.LOW:
                score -= 2
        
        # Deduct for complexity
        complexity = result.metrics.get('complexity_score', 0)
        if complexity > 50:
            score -= 20
        elif complexity > 30:
            score -= 10
        elif complexity > 15:
            score -= 5
        
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _generate_recommendations(self, issues: List[Issue]) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Group issues by category
        categories = {}
        for issue in issues:
            cat = issue.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(issue)
        
        # Generate recommendations
        if 'Error Handling' in categories:
            count = len(categories['Error Handling'])
            recommendations.append(f"Add fault handlers to {count} element(s) to improve error handling")
        
        if 'Governor Limits' in categories:
            recommendations.append("Review DML operations to ensure they are bulkified and outside loops")
        
        if 'Security' in categories:
            recommendations.append("Conduct security review for data access patterns and sharing rules")
        
        if 'Maintainability' in categories:
            recommendations.append("Externalize hardcoded values using Custom Metadata Types")
        
        if 'Documentation' in categories:
            recommendations.append("Add descriptions to the flow and key elements for better maintainability")
        
        return recommendations
    
    def _generate_documentation(self, metadata: Dict, result: AnalysisResult) -> str:
        """Generate comprehensive documentation"""
        docs = []
        details = result.details
        
        # Overview
        docs.append(f"## {result.metadata_name}")
        docs.append(f"\n### Overview")
        docs.append(f"- **Type:** {details['type']}")
        docs.append(f"- **Status:** {details['status']}")
        docs.append(f"- **API Version:** {details['api_version']}")
        
        if details.get('trigger_object'):
            docs.append(f"- **Trigger Object:** {details['trigger_object']}")
            docs.append(f"- **Trigger Type:** {details['trigger_type']}")
        
        # Entry Conditions
        if details.get('entry_conditions'):
            docs.append("\n### Entry Conditions")
            for cond in details['entry_conditions']:
                docs.append(f"- {cond['field']} {cond['operator']} '{cond['value']}'")
        
        # Elements
        docs.append("\n### Flow Elements")
        for elem_type, count in details['elements'].items():
            if count > 0:
                docs.append(f"- **{elem_type.replace('_', ' ').title()}:** {count}")
        
        # Dependencies
        if result.dependencies:
            docs.append("\n### Dependencies")
            
            # Group by type
            dep_groups = {}
            for dep in result.dependencies:
                if dep.target_type not in dep_groups:
                    dep_groups[dep.target_type] = []
                dep_groups[dep.target_type].append(dep)
            
            for dep_type, deps in dep_groups.items():
                docs.append(f"\n**{dep_type}s:**")
                for dep in deps:
                    docs.append(f"- {dep.target_name} ({dep.relationship})")
        
        # Metrics
        docs.append("\n### Metrics")
        docs.append(f"- **Complexity Score:** {result.metrics.get('complexity_score', 'N/A')}")
        docs.append(f"- **Maintainability:** {result.metrics.get('maintainability_score', 'N/A')}")
        docs.append(f"- **Total Elements:** {result.metrics.get('total_elements', 'N/A')}")
        
        return "\n".join(docs)


# =============================================================================
# APEX ANALYSIS ENGINE
# =============================================================================

class ApexAnalysisEngine(BaseAnalysisEngine):
    """Engine for analyzing Apex code"""
    
    def get_supported_tasks(self) -> List[TaskType]:
        return [
            TaskType.APEX_ANALYSIS,
            TaskType.CODE_REVIEW,
            TaskType.SECURITY_REVIEW,
            TaskType.DEPENDENCY_MAPPING
        ]
    
    def analyze(self, metadata: Dict, options: Dict = None) -> AnalysisResult:
        """Analyze Apex class metadata"""
        options = options or {}
        
        result = AnalysisResult(
            task_type=options.get('task_type', TaskType.APEX_ANALYSIS),
            metadata_type=MetadataType.APEX_CLASS,
            metadata_name=metadata.get('Name', 'Unknown')
        )
        
        body = metadata.get('Body', '')
        
        if body:
            result.details = self._analyze_apex_body(body)
            result.issues = self._check_apex_issues(body, metadata)
            result.metrics = self._calculate_apex_metrics(body)
            result.summary = self._generate_apex_summary(result)
        
        return result
    
    def _analyze_apex_body(self, body: str) -> Dict:
        """Analyze Apex code body"""
        return {
            "line_count": body.count('\n') + 1,
            "has_test_methods": '@isTest' in body or '@IsTest' in body,
            "has_sharing": 'with sharing' in body.lower() or 'without sharing' in body.lower(),
            "has_future": '@future' in body.lower(),
            "has_queueable": 'Queueable' in body,
            "has_batch": 'Database.Batchable' in body,
            "has_schedulable": 'Schedulable' in body,
            "soql_queries": len(re.findall(r'\[SELECT', body, re.IGNORECASE)),
            "dml_statements": len(re.findall(r'\b(insert|update|delete|upsert)\b', body, re.IGNORECASE))
        }
    
    def _check_apex_issues(self, body: str, metadata: Dict) -> List[Issue]:
        """Check for Apex code issues"""
        issues = []
        
        # Check for SOQL in loops
        if re.search(r'for\s*\([^)]+\)[^{]*\{[^}]*\[SELECT', body, re.IGNORECASE | re.DOTALL):
            issues.append(Issue(
                severity=Severity.CRITICAL,
                category="Governor Limits",
                message="Potential SOQL query inside a loop detected",
                recommendation="Move SOQL queries outside of loops and use collections"
            ))
        
        # Check for DML in loops
        if re.search(r'for\s*\([^)]+\)[^{]*\{[^}]*(insert|update|delete|upsert)', body, re.IGNORECASE | re.DOTALL):
            issues.append(Issue(
                severity=Severity.CRITICAL,
                category="Governor Limits",
                message="Potential DML statement inside a loop detected",
                recommendation="Collect records and perform DML operations outside of loops"
            ))
        
        # Check for missing sharing declaration
        if 'class' in body.lower() and 'sharing' not in body.lower():
            issues.append(Issue(
                severity=Severity.MEDIUM,
                category="Security",
                message="Class does not declare sharing mode",
                recommendation="Explicitly declare 'with sharing' or 'without sharing'"
            ))
        
        # Check for hardcoded IDs
        if re.search(r"'[a-zA-Z0-9]{15,18}'", body):
            issues.append(Issue(
                severity=Severity.HIGH,
                category="Maintainability",
                message="Hardcoded Salesforce IDs detected",
                recommendation="Use Custom Settings or Custom Metadata instead of hardcoded IDs"
            ))
        
        return issues
    
    def _calculate_apex_metrics(self, body: str) -> Dict:
        """Calculate Apex code metrics"""
        return {
            "lines_of_code": body.count('\n') + 1,
            "method_count": len(re.findall(r'(public|private|protected|global)\s+\w+\s+\w+\s*\(', body)),
            "soql_count": len(re.findall(r'\[SELECT', body, re.IGNORECASE)),
            "dml_count": len(re.findall(r'\b(insert|update|delete|upsert)\b', body, re.IGNORECASE)),
            "comment_lines": len(re.findall(r'(//|/\*|\*)', body))
        }
    
    def _generate_apex_summary(self, result: AnalysisResult) -> str:
        """Generate summary for Apex analysis"""
        details = result.details
        metrics = result.metrics
        
        summary = f"Apex class with {metrics['lines_of_code']} lines of code "
        summary += f"containing {metrics['method_count']} methods. "
        
        if details.get('has_test_methods'):
            summary += "This is a test class. "
        
        if metrics['soql_count'] > 0:
            summary += f"Contains {metrics['soql_count']} SOQL queries. "
        
        if metrics['dml_count'] > 0:
            summary += f"Contains {metrics['dml_count']} DML operations."
        
        return summary


# =============================================================================
# UNIFIED AI MODEL
# =============================================================================

class SalesforceMetadataAIModel:
    """
    Unified AI Model for Salesforce Metadata Analysis
    
    This model can:
    1. Analyze Flows, Apex, Objects, and other metadata
    2. Map dependencies across the org
    3. Perform impact analysis
    4. Generate documentation
    5. Conduct security and code reviews
    6. Provide optimization recommendations
    
    Works standalone with rule-based analysis or enhanced with LLM integration.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the AI Model
        
        Args:
            llm_client: Optional LLM client for enhanced analysis
        """
        self.llm_client = llm_client
        
        # Initialize analysis engines
        self.engines: Dict[MetadataType, BaseAnalysisEngine] = {
            MetadataType.FLOW: FlowAnalysisEngine(),
            MetadataType.APEX_CLASS: ApexAnalysisEngine(),
        }
        
        # Knowledge base for patterns and best practices
        self.knowledge_base = self._initialize_knowledge_base()
        
        # Cache for analysis results
        self.cache: Dict[str, AnalysisResult] = {}
        
        # Dependency graph
        self.dependency_graph: Dict[str, List[Dependency]] = {}
    
    def _initialize_knowledge_base(self) -> Dict:
        """Initialize knowledge base with patterns and best practices"""
        return {
            "flow_patterns": {
                "record_triggered": {
                    "best_practices": [
                        "Use entry conditions to filter records",
                        "Bulkify operations",
                        "Add fault handlers for actions",
                        "Use scheduled paths for delayed execution"
                    ],
                    "common_issues": [
                        "DML in loops",
                        "Missing error handling",
                        "Infinite loop triggers"
                    ]
                },
                "screen_flow": {
                    "best_practices": [
                        "Minimize screens for better UX",
                        "Use input validation",
                        "Handle back navigation"
                    ]
                }
            },
            "apex_patterns": {
                "trigger_handler": {
                    "best_practices": [
                        "One trigger per object",
                        "Use handler classes",
                        "Implement recursion prevention"
                    ]
                },
                "batch": {
                    "best_practices": [
                        "Implement start, execute, finish methods",
                        "Handle state across batches",
                        "Implement error handling"
                    ]
                }
            },
            "security": {
                "sharing_rules": [
                    "Default to 'with sharing'",
                    "Document 'without sharing' usage",
                    "Consider running user context"
                ],
                "field_level_security": [
                    "Check CRUD permissions",
                    "Use Security.stripInaccessible()",
                    "Validate input data"
                ]
            }
        }
    
    def analyze(
        self,
        metadata: Dict,
        task: TaskType = TaskType.FLOW_ANALYSIS,
        metadata_type: MetadataType = None,
        options: Dict = None
    ) -> AnalysisResult:
        """
        Perform analysis on metadata
        
        Args:
            metadata: The metadata to analyze (JSON/Dict format)
            task: Type of analysis task
            metadata_type: Type of metadata (auto-detected if not provided)
            options: Additional options for analysis
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        options = options or {}
        options['task_type'] = task
        
        # Auto-detect metadata type
        if metadata_type is None:
            metadata_type = self._detect_metadata_type(metadata)
        
        # Get appropriate engine
        engine = self.engines.get(metadata_type)
        
        if engine is None:
            return AnalysisResult(
                task_type=task,
                metadata_type=metadata_type,
                metadata_name="Unknown",
                success=False,
                summary=f"No analysis engine available for {metadata_type.value}"
            )
        
        # Run rule-based analysis
        result = engine.analyze(metadata, options)
        
        # Enhance with LLM if available
        if self.llm_client and options.get('use_llm', True):
            result = self._enhance_with_llm(result, metadata, task)
        
        # Cache result
        cache_key = self._generate_cache_key(metadata, task)
        self.cache[cache_key] = result
        
        # Update dependency graph
        self._update_dependency_graph(result)
        
        return result
    
    def _detect_metadata_type(self, metadata: Dict) -> MetadataType:
        """Auto-detect metadata type from structure"""
        # Check attributes
        if 'attributes' in metadata:
            type_name = metadata['attributes'].get('type', '')
            for mt in MetadataType:
                if mt.value.lower() == type_name.lower():
                    return mt
        
        # Check for Flow structure
        if 'Metadata' in metadata:
            inner = metadata['Metadata']
            if any(k in inner for k in ['actionCalls', 'decisions', 'start', 'processType']):
                return MetadataType.FLOW
        
        # Check for Apex structure
        if 'Body' in metadata and 'Name' in metadata:
            return MetadataType.APEX_CLASS
        
        return MetadataType.FLOW  # Default
    
    def _generate_cache_key(self, metadata: Dict, task: TaskType) -> str:
        """Generate cache key for analysis result"""
        content = json.dumps(metadata, sort_keys=True)
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{task.value}_{hash_val}"
    
    def _enhance_with_llm(
        self,
        result: AnalysisResult,
        metadata: Dict,
        task: TaskType
    ) -> AnalysisResult:
        """Enhance analysis with LLM capabilities"""
        if not self.llm_client:
            return result
        
        try:
            # Generate appropriate prompt based on task
            prompt = self._generate_llm_prompt(result, metadata, task)
            
            # Get LLM response
            llm_response = self.llm_client.analyze(prompt)
            
            # Parse and merge LLM insights
            result = self._merge_llm_insights(result, llm_response)
            
        except Exception as e:
            # LLM enhancement is optional, continue with rule-based results
            result.details['llm_error'] = str(e)
        
        return result
    
    def _generate_llm_prompt(
        self,
        result: AnalysisResult,
        metadata: Dict,
        task: TaskType
    ) -> str:
        """Generate task-specific LLM prompt"""
        base_context = f"""
Analyze this Salesforce {result.metadata_type.value}:
Name: {result.metadata_name}
Type: {result.details.get('type', 'Unknown')}

Current Analysis Summary:
{result.summary}

Issues Found:
{json.dumps([{"severity": i.severity.value, "message": i.message} for i in result.issues], indent=2)}

Dependencies:
{json.dumps([{"target": d.target_name, "relationship": d.relationship} for d in result.dependencies], indent=2)}
"""
        
        task_prompts = {
            TaskType.FLOW_ANALYSIS: "Provide a comprehensive analysis of this Flow including business logic, potential issues, and recommendations.",
            TaskType.CODE_REVIEW: "Perform a detailed code review focusing on best practices, performance, and maintainability.",
            TaskType.SECURITY_REVIEW: "Conduct a security review identifying vulnerabilities, data access patterns, and compliance concerns.",
            TaskType.OPTIMIZATION: "Identify optimization opportunities for performance, governor limits, and user experience.",
            TaskType.DOCUMENTATION: "Generate comprehensive technical documentation for this component.",
            TaskType.IMPACT_ANALYSIS: "Analyze the potential impact of modifying this component on other parts of the system."
        }
        
        return base_context + "\n\nTask: " + task_prompts.get(task, "Provide general analysis and recommendations.")
    
    def _merge_llm_insights(self, result: AnalysisResult, llm_response: str) -> AnalysisResult:
        """Merge LLM insights into analysis result"""
        result.details['llm_insights'] = llm_response
        
        # Append LLM response to documentation
        if result.documentation:
            result.documentation += f"\n\n## AI-Generated Insights\n{llm_response}"
        else:
            result.documentation = f"## AI-Generated Insights\n{llm_response}"
        
        return result
    
    def _update_dependency_graph(self, result: AnalysisResult):
        """Update global dependency graph"""
        key = f"{result.metadata_type.value}:{result.metadata_name}"
        self.dependency_graph[key] = result.dependencies
    
    def get_impact_analysis(
        self,
        metadata_type: str,
        name: str,
        change_description: str
    ) -> AnalysisResult:
        """
        Analyze impact of a proposed change
        
        Args:
            metadata_type: Type of metadata being changed
            name: Name of the metadata component
            change_description: Description of the proposed change
            
        Returns:
            AnalysisResult with impact analysis
        """
        result = AnalysisResult(
            task_type=TaskType.IMPACT_ANALYSIS,
            metadata_type=MetadataType(metadata_type) if metadata_type in [m.value for m in MetadataType] else MetadataType.FLOW,
            metadata_name=name
        )
        
        # Find all dependents
        key = f"{metadata_type}:{name}"
        impacted = []
        
        for source_key, deps in self.dependency_graph.items():
            for dep in deps:
                if f"{dep.target_type}:{dep.target_name}" == key:
                    impacted.append({
                        "component": source_key,
                        "relationship": dep.relationship
                    })
        
        result.details = {
            "change_target": name,
            "change_description": change_description,
            "impacted_components": impacted,
            "impact_count": len(impacted)
        }
        
        # Calculate risk level
        if len(impacted) > 10:
            risk = "CRITICAL"
        elif len(impacted) > 5:
            risk = "HIGH"
        elif len(impacted) > 2:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        result.summary = f"Changing {name} will impact {len(impacted)} component(s). Risk level: {risk}"
        result.metrics = {"risk_level": risk, "impact_count": len(impacted)}
        
        # Generate recommendations
        if risk in ["CRITICAL", "HIGH"]:
            result.recommendations = [
                "Create detailed test plan covering all impacted components",
                "Consider staged rollout",
                "Prepare rollback plan",
                "Notify all stakeholders"
            ]
        
        return result
    
    def batch_analyze(
        self,
        metadata_list: List[Dict],
        task: TaskType = TaskType.FLOW_ANALYSIS
    ) -> List[AnalysisResult]:
        """
        Analyze multiple metadata items
        
        Args:
            metadata_list: List of metadata dictionaries
            task: Analysis task type
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        for metadata in metadata_list:
            result = self.analyze(metadata, task)
            results.append(result)
        return results
    
    def generate_org_report(self) -> str:
        """Generate comprehensive org-wide analysis report"""
        report = []
        report.append("# Salesforce Org Analysis Report")
        report.append(f"\n**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Components Analyzed:** {len(self.cache)}")
        
        # Summary statistics
        all_issues = []
        all_deps = []
        
        for result in self.cache.values():
            all_issues.extend(result.issues)
            all_deps.extend(result.dependencies)
        
        report.append("\n## Summary")
        report.append(f"- Total Issues: {len(all_issues)}")
        report.append(f"- Critical Issues: {len([i for i in all_issues if i.severity == Severity.CRITICAL])}")
        report.append(f"- High Issues: {len([i for i in all_issues if i.severity == Severity.HIGH])}")
        report.append(f"- Total Dependencies: {len(all_deps)}")
        
        # Issues by category
        report.append("\n## Issues by Category")
        categories = {}
        for issue in all_issues:
            cat = issue.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(issue)
        
        for cat, issues in sorted(categories.items(), key=lambda x: -len(x[1])):
            report.append(f"\n### {cat} ({len(issues)} issues)")
            for issue in issues[:5]:  # Top 5
                report.append(f"- [{issue.severity.value.upper()}] {issue.message}")
        
        # Dependency diagram
        report.append("\n## Dependency Overview")
        report.append("\n```mermaid")
        report.append("graph TD")
        
        seen = set()
        for deps in self.dependency_graph.values():
            for dep in deps[:20]:  # Limit for readability
                edge = f"{dep.source_name} --> {dep.target_name}"
                if edge not in seen:
                    seen.add(edge)
                    source_id = dep.source_name.replace(" ", "_").replace("-", "_")
                    target_id = dep.target_name.replace(" ", "_").replace("-", "_")
                    report.append(f"    {source_id}[{dep.source_name}] -->|{dep.relationship}| {target_id}[{dep.target_name}]")
        
        report.append("```")
        
        return "\n".join(report)
    
    def query(self, question: str, context_metadata: Dict = None) -> str:
        """
        Answer questions about metadata using AI
        
        Args:
            question: Natural language question
            context_metadata: Optional specific metadata to query about
            
        Returns:
            Answer string
        """
        if not self.llm_client:
            return "LLM client required for natural language queries. Using rule-based analysis instead."
        
        # Build context from cache
        context = "Available analysis data:\n"
        for key, result in list(self.cache.items())[:5]:
            context += f"- {result.metadata_name}: {result.summary}\n"
        
        # Extract and include the ACTUAL flow metadata JSON for accurate analysis
        metadata_json_str = ""
        if context_metadata:
            # Analyze provided metadata first
            result = self.analyze(context_metadata)
            context += f"\nCurrent analysis:\n{result.summary}\n"
            
            # Extract the key flow metadata sections that contain actual values
            inner = context_metadata.get('Metadata', context_metadata)
            flow_details = {}
            
            # Include critical sections with real values
            for key_section in ['start', 'decisions', 'actionCalls', 'recordCreates',
                                'recordUpdates', 'recordLookups', 'recordDeletes',
                                'assignments', 'loops', 'screens', 'formulas',
                                'variables', 'processType', 'label', 'description',
                                'startElementReference', 'status']:
                if key_section in inner and inner[key_section]:
                    flow_details[key_section] = inner[key_section]
            
            # Include flow name
            flow_name = context_metadata.get('FullName', context_metadata.get('fullName', 'Unknown'))
            flow_details['flowName'] = flow_name
            
            # Serialize the actual metadata (truncate if too large)
            raw_json = json.dumps(flow_details, indent=2, default=str)
            if len(raw_json) > 15000:
                raw_json = raw_json[:15000] + "\n... [truncated]"
            
            metadata_json_str = f"""

=== ACTUAL FLOW METADATA (Source of Truth) ===
IMPORTANT: Base your answer ONLY on the actual values in this metadata.
Do NOT infer, guess, or use any other source. Every field name, operator,
value, and condition below is the exact data from the Salesforce org.

{raw_json}
=== END OF FLOW METADATA ===
"""
        
        prompt = f"""You are a Salesforce Flow expert analyzer. You MUST answer based ONLY on
the actual flow metadata provided below. Do NOT make up values or guess.
If a field has a specific value in the metadata (e.g., a filter value,
a decision threshold, a trigger condition), you MUST quote that exact value.

{context}
{metadata_json_str}

Question: {question}

RULES:
1. Use ONLY the actual metadata values provided above
2. Quote exact field names, operators, and values from the metadata
3. If the metadata doesn't contain enough information, say so
4. Never fabricate or assume values not present in the metadata
"""
        
        return self.llm_client.analyze(prompt)


# =============================================================================
# FACTORY AND HELPERS
# =============================================================================

def create_model(llm_provider: str = None, **kwargs) -> SalesforceMetadataAIModel:
    """
    Factory function to create the AI model
    
    Args:
        llm_provider: Optional LLM provider ('openai', 'azure', 'anthropic', 'github')
        **kwargs: Additional arguments for LLM client
        
    Returns:
        Configured SalesforceMetadataAIModel
    """
    llm_client = None
    
    # Try to load from config if no provider specified
    if llm_provider is None:
        try:
            from config import get_config
            config = get_config()
            llm_config = config.get_llm_config()
            
            if llm_config:
                llm_provider = llm_config.get('provider')
                # Handle GitHub token -> api_key mapping
                if 'token' in llm_config:
                    llm_config['api_key'] = llm_config.pop('token')
                kwargs.update({k: v for k, v in llm_config.items() if k != 'provider'})
        except ImportError:
            pass
    
    # Handle token -> api_key in kwargs as well
    if 'token' in kwargs:
        kwargs['api_key'] = kwargs.pop('token')
    
    if llm_provider:
        try:
            from llm_integration import create_analyzer
            llm_client = create_analyzer(provider=llm_provider, **kwargs)
        except ImportError:
            print("Warning: LLM integration not available. Using rule-based analysis only.")
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}. Using rule-based analysis.")
    
    return SalesforceMetadataAIModel(llm_client=llm_client)


def create_model_from_config(env_path: str = None) -> SalesforceMetadataAIModel:
    """
    Create model using configuration from .env file
    
    Args:
        env_path: Optional path to .env file
        
    Returns:
        Configured SalesforceMetadataAIModel
    """
    try:
        from config import init_config
        config = init_config(env_path)
        config.print_status()
        
        llm_config = config.get_llm_config()
        
        if llm_config:
            # Handle GitHub token -> api_key mapping
            config_copy = dict(llm_config)
            if 'token' in config_copy:
                config_copy['api_key'] = config_copy.pop('token')
            
            return create_model(
                llm_provider=config_copy.get('provider'),
                **{k: v for k, v in config_copy.items() if k != 'provider'}
            )
        else:
            print("\n⚠️  No LLM configured. Using rule-based analysis only.")
            return create_model()
            
    except ImportError:
        print("Warning: Config module not available. Using defaults.")
        return create_model()


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Salesforce Metadata AI Model")
    print("=" * 60)
    
    # Create model from config
    model = create_model_from_config()
    
    # Demo with sample file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, 'r') as f:
            metadata = json.load(f)
        
        # Run comprehensive analysis
        result = model.analyze(metadata, TaskType.FLOW_ANALYSIS)
        print(result.to_markdown())
    else:
        print("\nUsage: python model.py <metadata_file.json>")
        print("\nSupported tasks:")
        for task in TaskType:
            print(f"  - {task.value}")

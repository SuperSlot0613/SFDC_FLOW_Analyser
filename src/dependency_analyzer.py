"""
Dependency Analyzer for Salesforce Metadata
============================================
Analyzes cross-dependencies between Flows, Apex, Objects, and Fields.
Provides impact analysis capabilities.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
from pathlib import Path


@dataclass
class Dependency:
    """Represents a dependency relationship"""
    source_type: str  # Flow, ApexClass, etc.
    source_name: str
    target_type: str
    target_name: str
    dependency_type: str  # 'calls', 'reads', 'writes', 'references'
    details: Optional[str] = None


@dataclass
class DependencyNode:
    """Node in the dependency graph"""
    metadata_type: str
    name: str
    dependencies: List[Dependency] = field(default_factory=list)
    dependents: List[Dependency] = field(default_factory=list)


class DependencyGraph:
    """
    Graph structure for tracking metadata dependencies
    """
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: List[Dependency] = []
    
    def add_node(self, metadata_type: str, name: str) -> DependencyNode:
        """Add a node to the graph"""
        key = f"{metadata_type}:{name}"
        if key not in self.nodes:
            self.nodes[key] = DependencyNode(metadata_type=metadata_type, name=name)
        return self.nodes[key]
    
    def add_dependency(self, dependency: Dependency):
        """Add a dependency edge to the graph"""
        source_key = f"{dependency.source_type}:{dependency.source_name}"
        target_key = f"{dependency.target_type}:{dependency.target_name}"
        
        # Ensure nodes exist
        if source_key not in self.nodes:
            self.add_node(dependency.source_type, dependency.source_name)
        if target_key not in self.nodes:
            self.add_node(dependency.target_type, dependency.target_name)
        
        # Add edge
        self.edges.append(dependency)
        self.nodes[source_key].dependencies.append(dependency)
        self.nodes[target_key].dependents.append(dependency)
    
    def get_dependencies(self, metadata_type: str, name: str) -> List[Dependency]:
        """Get all dependencies of a metadata item"""
        key = f"{metadata_type}:{name}"
        if key in self.nodes:
            return self.nodes[key].dependencies
        return []
    
    def get_dependents(self, metadata_type: str, name: str) -> List[Dependency]:
        """Get all items that depend on a metadata item"""
        key = f"{metadata_type}:{name}"
        if key in self.nodes:
            return self.nodes[key].dependents
        return []
    
    def get_impact_chain(self, metadata_type: str, name: str, depth: int = 5) -> Dict[str, Set[str]]:
        """
        Get full impact chain - what would be affected if this item changes
        Returns items grouped by depth level
        """
        key = f"{metadata_type}:{name}"
        if key not in self.nodes:
            return {}
        
        impacted = defaultdict(set)
        visited = set()
        
        def traverse(current_key: str, current_depth: int):
            if current_depth > depth or current_key in visited:
                return
            
            visited.add(current_key)
            node = self.nodes.get(current_key)
            
            if node:
                for dep in node.dependents:
                    dependent_key = f"{dep.source_type}:{dep.source_name}"
                    impacted[current_depth].add(dependent_key)
                    traverse(dependent_key, current_depth + 1)
        
        traverse(key, 1)
        return dict(impacted)
    
    def to_mermaid(self, filter_type: Optional[str] = None) -> str:
        """Generate Mermaid diagram syntax for visualization"""
        lines = ["graph TD"]
        
        for edge in self.edges:
            if filter_type and edge.source_type != filter_type and edge.target_type != filter_type:
                continue
            
            source_id = f"{edge.source_type}_{edge.source_name}".replace(" ", "_").replace("-", "_")
            target_id = f"{edge.target_type}_{edge.target_name}".replace(" ", "_").replace("-", "_")
            
            lines.append(f"    {source_id}[{edge.source_name}] -->|{edge.dependency_type}| {target_id}[{edge.target_name}]")
        
        return "\n".join(lines)
    
    def to_json(self) -> Dict:
        """Export graph as JSON"""
        return {
            "nodes": [
                {"type": n.metadata_type, "name": n.name}
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": {"type": e.source_type, "name": e.source_name},
                    "target": {"type": e.target_type, "name": e.target_name},
                    "relationship": e.dependency_type,
                    "details": e.details
                }
                for e in self.edges
            ]
        }


class FlowDependencyExtractor:
    """
    Extracts dependencies from Flow metadata
    """
    
    def __init__(self, flow_data: Dict):
        self.flow_data = flow_data
        self.metadata = flow_data.get('Metadata', {})
        self.flow_name = self._get_flow_name()
    
    def _get_flow_name(self) -> str:
        """Extract flow name"""
        label = self.metadata.get('label', '')
        interview = self.metadata.get('interviewLabel', '')
        if interview:
            return interview.replace(' {!$Flow.CurrentDateTime}', '').strip()
        return label or 'UnknownFlow'
    
    def extract_dependencies(self) -> List[Dependency]:
        """Extract all dependencies from the flow"""
        dependencies = []
        
        # Object dependencies from trigger
        dependencies.extend(self._extract_trigger_dependencies())
        
        # Apex dependencies from action calls
        dependencies.extend(self._extract_apex_dependencies())
        
        # Subflow dependencies
        dependencies.extend(self._extract_subflow_dependencies())
        
        # Field dependencies
        dependencies.extend(self._extract_field_dependencies())
        
        # Record operation dependencies
        dependencies.extend(self._extract_record_operation_dependencies())
        
        return dependencies
    
    def _extract_trigger_dependencies(self) -> List[Dependency]:
        """Extract object dependencies from trigger configuration"""
        deps = []
        start = self.metadata.get('start', {})
        
        if start.get('object'):
            deps.append(Dependency(
                source_type="Flow",
                source_name=self.flow_name,
                target_type="Object",
                target_name=start['object'],
                dependency_type="triggers_on",
                details=f"Trigger type: {start.get('triggerType', 'Unknown')}"
            ))
        
        return deps
    
    def _extract_apex_dependencies(self) -> List[Dependency]:
        """Extract Apex class dependencies from action calls"""
        deps = []
        
        for action in self.metadata.get('actionCalls', []):
            if action.get('actionType') == 'apex':
                class_name = action.get('actionName') or action.get('nameSegment')
                if class_name:
                    deps.append(Dependency(
                        source_type="Flow",
                        source_name=self.flow_name,
                        target_type="ApexClass",
                        target_name=class_name,
                        dependency_type="calls",
                        details=f"Action: {action.get('label', 'Unknown')}"
                    ))
        
        return deps
    
    def _extract_subflow_dependencies(self) -> List[Dependency]:
        """Extract subflow dependencies"""
        deps = []
        
        for subflow in self.metadata.get('subflows', []):
            flow_name = subflow.get('flowName')
            if flow_name:
                deps.append(Dependency(
                    source_type="Flow",
                    source_name=self.flow_name,
                    target_type="Flow",
                    target_name=flow_name,
                    dependency_type="calls_subflow",
                    details=f"Element: {subflow.get('label', 'Unknown')}"
                ))
        
        return deps
    
    def _extract_field_dependencies(self) -> List[Dependency]:
        """Extract field dependencies from all elements"""
        deps = []
        fields = set()
        
        # Helper to extract fields from value references
        def extract_fields(data: Any, prefix: str = ""):
            if isinstance(data, dict):
                for key in ['leftValueReference', 'elementReference', 'field']:
                    if data.get(key):
                        ref = data[key]
                        if isinstance(ref, str):
                            # Parse field references like $Record.Field__c
                            if '$Record.' in ref:
                                field_name = ref.replace('$Record.', '').split('.')[0]
                                fields.add((field_name, 'reads'))
                            elif '.' in ref:
                                parts = ref.split('.')
                                if len(parts) >= 2:
                                    fields.add((parts[-1], 'reads'))
                
                for value in data.values():
                    extract_fields(value)
            elif isinstance(data, list):
                for item in data:
                    extract_fields(item)
        
        # Extract from all metadata
        extract_fields(self.metadata)
        
        # Extract fields being written
        for update in self.metadata.get('recordUpdates', []):
            for assignment in update.get('inputAssignments', []):
                if assignment.get('field'):
                    fields.add((assignment['field'], 'writes'))
        
        for create in self.metadata.get('recordCreates', []):
            for assignment in create.get('inputAssignments', []):
                if assignment.get('field'):
                    fields.add((assignment['field'], 'writes'))
        
        # Create dependencies for each field
        trigger_object = self.metadata.get('start', {}).get('object', 'Unknown')
        for field_name, access_type in fields:
            deps.append(Dependency(
                source_type="Flow",
                source_name=self.flow_name,
                target_type="Field",
                target_name=f"{trigger_object}.{field_name}",
                dependency_type=access_type
            ))
        
        return deps
    
    def _extract_record_operation_dependencies(self) -> List[Dependency]:
        """Extract dependencies from record operations (CRUD)"""
        deps = []
        
        # Record lookups
        for lookup in self.metadata.get('recordLookups', []):
            obj = lookup.get('object')
            if obj:
                deps.append(Dependency(
                    source_type="Flow",
                    source_name=self.flow_name,
                    target_type="Object",
                    target_name=obj,
                    dependency_type="reads",
                    details=f"Lookup: {lookup.get('label', 'Unknown')}"
                ))
        
        # Record creates
        for create in self.metadata.get('recordCreates', []):
            obj = create.get('object')
            if obj:
                deps.append(Dependency(
                    source_type="Flow",
                    source_name=self.flow_name,
                    target_type="Object",
                    target_name=obj,
                    dependency_type="creates",
                    details=f"Create: {create.get('label', 'Unknown')}"
                ))
        
        # Record deletes
        for delete in self.metadata.get('recordDeletes', []):
            obj = delete.get('object')
            if obj:
                deps.append(Dependency(
                    source_type="Flow",
                    source_name=self.flow_name,
                    target_type="Object",
                    target_name=obj,
                    dependency_type="deletes",
                    details=f"Delete: {delete.get('label', 'Unknown')}"
                ))
        
        return deps


class ImpactAnalyzer:
    """
    Analyzes the impact of changes to metadata
    """
    
    def __init__(self, dependency_graph: DependencyGraph):
        self.graph = dependency_graph
    
    def analyze_field_change(self, object_name: str, field_name: str) -> Dict:
        """
        Analyze impact of changing or removing a field
        """
        field_key = f"{object_name}.{field_name}"
        
        impacted_items = {
            "directly_affected": [],
            "indirectly_affected": [],
            "risk_level": "LOW"
        }
        
        # Find all items that reference this field
        for node in self.graph.nodes.values():
            for dep in node.dependencies:
                if dep.target_type == "Field" and field_key in dep.target_name:
                    impacted_items["directly_affected"].append({
                        "type": dep.source_type,
                        "name": dep.source_name,
                        "usage": dep.dependency_type
                    })
        
        # Calculate risk based on number of affected items
        affected_count = len(impacted_items["directly_affected"])
        if affected_count > 10:
            impacted_items["risk_level"] = "HIGH"
        elif affected_count > 3:
            impacted_items["risk_level"] = "MEDIUM"
        
        return impacted_items
    
    def analyze_apex_change(self, class_name: str) -> Dict:
        """
        Analyze impact of changing an Apex class
        """
        impact_chain = self.graph.get_impact_chain("ApexClass", class_name)
        
        return {
            "class_name": class_name,
            "affected_flows": [
                item for level_items in impact_chain.values()
                for item in level_items
                if item.startswith("Flow:")
            ],
            "impact_depth": len(impact_chain),
            "total_affected": sum(len(items) for items in impact_chain.values())
        }
    
    def generate_impact_report(self, metadata_type: str, name: str, change_description: str) -> str:
        """
        Generate a comprehensive impact report
        """
        report = []
        report.append(f"# Impact Analysis Report")
        report.append(f"\n## Change Target")
        report.append(f"- **Type:** {metadata_type}")
        report.append(f"- **Name:** {name}")
        report.append(f"- **Proposed Change:** {change_description}")
        
        # Get impact chain
        impact = self.graph.get_impact_chain(metadata_type, name)
        
        report.append(f"\n## Impact Summary")
        report.append(f"- **Depth of Impact:** {len(impact)} levels")
        total_items = sum(len(items) for items in impact.values())
        report.append(f"- **Total Items Affected:** {total_items}")
        
        # Risk assessment
        risk = "LOW"
        if total_items > 20:
            risk = "CRITICAL"
        elif total_items > 10:
            risk = "HIGH"
        elif total_items > 3:
            risk = "MEDIUM"
        
        report.append(f"- **Risk Level:** {risk}")
        
        report.append(f"\n## Affected Items by Level")
        for level, items in sorted(impact.items()):
            report.append(f"\n### Level {level} (Direct {'Dependents' if level == 1 else 'Chain'})")
            for item in items:
                report.append(f"- {item}")
        
        # Direct dependencies
        deps = self.graph.get_dependencies(metadata_type, name)
        if deps:
            report.append(f"\n## Dependencies of {name}")
            for dep in deps:
                report.append(f"- {dep.dependency_type} → {dep.target_type}:{dep.target_name}")
        
        report.append(f"\n## Recommendations")
        if risk == "CRITICAL" or risk == "HIGH":
            report.append("- ⚠️ High-impact change - requires thorough testing")
            report.append("- Create detailed test plan covering all affected items")
            report.append("- Consider staged rollout")
            report.append("- Prepare rollback plan")
        elif risk == "MEDIUM":
            report.append("- Standard testing recommended")
            report.append("- Notify teams responsible for affected items")
        else:
            report.append("- Standard change process applies")
        
        return "\n".join(report)


def build_dependency_graph(flow_data_list: List[Dict]) -> DependencyGraph:
    """
    Build a complete dependency graph from multiple flow metadata files
    """
    graph = DependencyGraph()
    
    for flow_data in flow_data_list:
        extractor = FlowDependencyExtractor(flow_data)
        
        # Add flow node
        graph.add_node("Flow", extractor.flow_name)
        
        # Add all dependencies
        for dep in extractor.extract_dependencies():
            graph.add_dependency(dep)
    
    return graph

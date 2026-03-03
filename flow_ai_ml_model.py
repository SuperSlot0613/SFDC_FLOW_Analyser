"""
Salesforce Flow AI/ML Model
============================
A comprehensive AI/ML model for Salesforce Flow analysis, understanding, and testing.

This model can:
1. Be trained on flow patterns
2. Perform inference for flow analysis
3. Generate test scenarios
4. Detect anomalies and regressions
5. Provide natural language explanations

Architecture:
- Pattern Recognition Layer: Learns flow structures
- Decision Analysis Layer: Understands decision logic
- NLU Layer: Natural language understanding for queries
- Generation Layer: Creates scenarios and explanations
- Validation Layer: Checks best practices

Author: Flow AI Implementation
Version: 2.0.0
"""

import json
import os
import re
import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import math


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class ModelTask(Enum):
    """Tasks the model can perform"""
    FLOW_ANALYSIS = "flow_analysis"
    DECISION_EXTRACTION = "decision_extraction"
    TRIGGER_ANALYSIS = "trigger_analysis"
    SCENARIO_GENERATION = "scenario_generation"
    QUERY_ANSWERING = "query_answering"
    REGRESSION_DETECTION = "regression_detection"
    BEST_PRACTICE_CHECK = "best_practice_check"
    IMPACT_PREDICTION = "impact_prediction"
    FLOW_EXPLANATION = "flow_explanation"
    ANOMALY_DETECTION = "anomaly_detection"


class FlowElementType(Enum):
    """Types of flow elements"""
    DECISION = "decision"
    RECORD_LOOKUP = "record_lookup"
    RECORD_CREATE = "record_create"
    RECORD_UPDATE = "record_update"
    RECORD_DELETE = "record_delete"
    SCREEN = "screen"
    APEX_ACTION = "apex_action"
    EMAIL_ALERT = "email_alert"
    SUBFLOW = "subflow"
    LOOP = "loop"
    ASSIGNMENT = "assignment"
    WAIT = "wait"


class Severity(Enum):
    """Severity levels for issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FlowPattern:
    """Represents a learned flow pattern"""
    pattern_id: str
    pattern_type: str
    frequency: int = 0
    confidence: float = 0.0
    examples: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ModelPrediction:
    """Model prediction result"""
    task: ModelTask
    prediction: Any
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TrainingExample:
    """Training example for the model"""
    input_data: Dict
    expected_output: Any
    task: ModelTask
    weight: float = 1.0


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    total_predictions: int = 0
    correct_predictions: int = 0
    task_metrics: Dict[str, Dict] = field(default_factory=dict)


# =============================================================================
# FEATURE EXTRACTORS
# =============================================================================

class FlowFeatureExtractor:
    """Extracts features from Salesforce Flow metadata"""
    
    def __init__(self):
        self.feature_cache = {}
    
    def extract(self, flow_data: Dict) -> Dict[str, Any]:
        """Extract all features from a flow"""
        flow_id = self._get_flow_id(flow_data)
        
        if flow_id in self.feature_cache:
            return self.feature_cache[flow_id]
        
        features = {
            # Basic features
            "flow_type": self._extract_flow_type(flow_data),
            "element_count": self._count_elements(flow_data),
            "complexity_score": self._calculate_complexity(flow_data),
            
            # Structural features
            "decisions": self._extract_decisions(flow_data),
            "record_operations": self._extract_record_ops(flow_data),
            "triggers": self._extract_triggers(flow_data),
            "screens": self._extract_screens(flow_data),
            "apex_calls": self._extract_apex_calls(flow_data),
            
            # Semantic features
            "objects_used": self._extract_objects(flow_data),
            "fields_used": self._extract_fields(flow_data),
            "variables": self._extract_variables(flow_data),
            "formulas": self._extract_formulas(flow_data),
            
            # Pattern features
            "has_error_handling": self._has_error_handling(flow_data),
            "has_null_checks": self._has_null_checks(flow_data),
            "has_loops": self._has_loops(flow_data),
            "branching_factor": self._calculate_branching(flow_data),
            
            # Risk features
            "hardcoded_values": self._find_hardcoded_values(flow_data),
            "missing_fault_paths": self._find_missing_faults(flow_data),
        }
        
        self.feature_cache[flow_id] = features
        return features
    
    def _get_flow_id(self, flow_data: Dict) -> str:
        """Get unique flow identifier"""
        return flow_data.get('FullName', '') or flow_data.get('Id', str(hash(str(flow_data))))
    
    def _extract_flow_type(self, flow_data: Dict) -> str:
        """Extract flow process type"""
        return flow_data.get('ProcessType', 'Unknown')
    
    def _count_elements(self, flow_data: Dict) -> Dict[str, int]:
        """Count elements by type"""
        metadata = flow_data.get('Metadata', {})
        return {
            'decisions': len(metadata.get('decisions', [])),
            'record_lookups': len(metadata.get('recordLookups', [])),
            'record_creates': len(metadata.get('recordCreates', [])),
            'record_updates': len(metadata.get('recordUpdates', [])),
            'record_deletes': len(metadata.get('recordDeletes', [])),
            'screens': len(metadata.get('screens', [])),
            'action_calls': len(metadata.get('actionCalls', [])),
            'assignments': len(metadata.get('assignments', [])),
            'loops': len(metadata.get('loops', [])),
            'subflows': len(metadata.get('subflows', [])),
        }
    
    def _calculate_complexity(self, flow_data: Dict) -> float:
        """Calculate flow complexity score (0-100)"""
        counts = self._count_elements(flow_data)
        
        # Weighted complexity calculation
        weights = {
            'decisions': 3.0,
            'record_lookups': 2.0,
            'record_creates': 2.5,
            'record_updates': 2.5,
            'screens': 1.5,
            'action_calls': 4.0,  # Apex is complex
            'loops': 3.5,
            'subflows': 2.0,
        }
        
        score = sum(counts.get(k, 0) * w for k, w in weights.items())
        
        # Normalize to 0-100
        return min(100, score)
    
    def _extract_decisions(self, flow_data: Dict) -> List[Dict]:
        """Extract decision information"""
        metadata = flow_data.get('Metadata', {})
        decisions = []
        
        for dec in metadata.get('decisions', []):
            decision_info = {
                'name': dec.get('name'),
                'label': dec.get('label'),
                'rules': [],
                'has_default': bool(dec.get('defaultConnector'))
            }
            
            for rule in dec.get('rules', []):
                rule_info = {
                    'name': rule.get('name'),
                    'conditions': [],
                    'logic': rule.get('conditionLogic', 'and')
                }
                
                for cond in rule.get('conditions', []):
                    rule_info['conditions'].append({
                        'left': cond.get('leftValueReference', ''),
                        'operator': cond.get('operator', ''),
                        'right': self._extract_value(cond.get('rightValue', {}))
                    })
                
                decision_info['rules'].append(rule_info)
            
            decisions.append(decision_info)
        
        return decisions
    
    def _extract_record_ops(self, flow_data: Dict) -> List[Dict]:
        """Extract record operations"""
        metadata = flow_data.get('Metadata', {})
        ops = []
        
        for lookup in metadata.get('recordLookups', []):
            ops.append({
                'type': 'lookup',
                'name': lookup.get('name'),
                'object': lookup.get('object'),
                'filters': len(lookup.get('filters', [])),
            })
        
        for create in metadata.get('recordCreates', []):
            ops.append({
                'type': 'create',
                'name': create.get('name'),
                'object': create.get('object'),
                'fields': len(create.get('inputAssignments', [])),
            })
        
        for update in metadata.get('recordUpdates', []):
            ops.append({
                'type': 'update',
                'name': update.get('name'),
                'object': update.get('object') or update.get('inputReference', ''),
                'fields': len(update.get('inputAssignments', [])),
            })
        
        return ops
    
    def _extract_triggers(self, flow_data: Dict) -> Dict:
        """Extract trigger configuration"""
        metadata = flow_data.get('Metadata', {})
        start = metadata.get('start', {})
        
        if not start:
            return {'type': None, 'object': None, 'conditions': []}
        
        conditions = []
        for f in start.get('filters', []):
            conditions.append({
                'field': f.get('field'),
                'operator': f.get('operator'),
                'value': self._extract_value(f.get('value', {}))
            })
        
        return {
            'type': start.get('triggerType'),
            'object': start.get('object'),
            'record_trigger_type': start.get('recordTriggerType'),
            'conditions': conditions
        }
    
    def _extract_screens(self, flow_data: Dict) -> List[Dict]:
        """Extract screen information"""
        metadata = flow_data.get('Metadata', {})
        screens = []
        
        for screen in metadata.get('screens', []):
            screen_info = {
                'name': screen.get('name'),
                'label': screen.get('label'),
                'fields': [],
                'required_count': 0
            }
            
            for field in screen.get('fields', []):
                field_info = {
                    'name': field.get('name'),
                    'type': field.get('fieldType'),
                    'required': field.get('isRequired', False)
                }
                screen_info['fields'].append(field_info)
                if field_info['required']:
                    screen_info['required_count'] += 1
            
            screens.append(screen_info)
        
        return screens
    
    def _extract_apex_calls(self, flow_data: Dict) -> List[Dict]:
        """Extract Apex action calls"""
        metadata = flow_data.get('Metadata', {})
        calls = []
        
        for action in metadata.get('actionCalls', []):
            if action.get('actionType') == 'apex':
                calls.append({
                    'name': action.get('name'),
                    'action_name': action.get('actionName'),
                    'has_fault_path': bool(action.get('faultConnector'))
                })
        
        return calls
    
    def _extract_objects(self, flow_data: Dict) -> List[str]:
        """Extract all Salesforce objects used"""
        objects = set()
        metadata = flow_data.get('Metadata', {})
        if not metadata:
            return list(objects)
        
        # From trigger
        start = metadata.get('start') or {}
        if start and start.get('object'):
            objects.add(start['object'])
        
        # From record operations
        for lookup in metadata.get('recordLookups', []):
            if lookup.get('object'):
                objects.add(lookup['object'])
        
        for create in metadata.get('recordCreates', []):
            if create.get('object'):
                objects.add(create['object'])
        
        for update in metadata.get('recordUpdates', []):
            if update.get('object'):
                objects.add(update['object'])
        
        return list(objects)
    
    def _extract_fields(self, flow_data: Dict) -> List[str]:
        """Extract all fields referenced"""
        fields = set()
        metadata = flow_data.get('Metadata', {})
        if not metadata:
            return list(fields)
        
        # From filters
        start = metadata.get('start') or {}
        if start:
            for f in start.get('filters') or []:
                if f and f.get('field'):
                    fields.add(f['field'])
        
        # From record lookups
        for lookup in metadata.get('recordLookups', []):
            for f in lookup.get('filters', []):
                if f.get('field'):
                    fields.add(f['field'])
        
        return list(fields)
    
    def _extract_variables(self, flow_data: Dict) -> List[Dict]:
        """Extract flow variables"""
        metadata = flow_data.get('Metadata', {})
        variables = []
        
        for var in metadata.get('variables', []):
            variables.append({
                'name': var.get('name'),
                'data_type': var.get('dataType'),
                'is_input': var.get('isInput', False),
                'is_output': var.get('isOutput', False)
            })
        
        return variables
    
    def _extract_formulas(self, flow_data: Dict) -> List[Dict]:
        """Extract formula resources"""
        metadata = flow_data.get('Metadata', {})
        formulas = []
        
        for formula in metadata.get('formulas', []):
            formulas.append({
                'name': formula.get('name'),
                'expression': formula.get('expression'),
                'data_type': formula.get('dataType')
            })
        
        return formulas
    
    def _has_error_handling(self, flow_data: Dict) -> bool:
        """Check if flow has error handling"""
        metadata = flow_data.get('Metadata', {})
        
        # Check for fault connectors
        for action in metadata.get('actionCalls', []):
            if action.get('faultConnector'):
                return True
        
        for create in metadata.get('recordCreates', []):
            if create.get('faultConnector'):
                return True
        
        return False
    
    def _has_null_checks(self, flow_data: Dict) -> bool:
        """Check if flow has null checks in decisions"""
        metadata = flow_data.get('Metadata', {})
        
        for decision in metadata.get('decisions', []):
            for rule in decision.get('rules', []):
                for cond in rule.get('conditions', []):
                    if cond.get('operator') == 'IsNull':
                        return True
        
        return False
    
    def _has_loops(self, flow_data: Dict) -> bool:
        """Check if flow has loops"""
        metadata = flow_data.get('Metadata', {})
        return len(metadata.get('loops', [])) > 0
    
    def _calculate_branching(self, flow_data: Dict) -> float:
        """Calculate branching factor (average paths per decision)"""
        metadata = flow_data.get('Metadata', {})
        decisions = metadata.get('decisions', [])
        
        if not decisions:
            return 0.0
        
        total_paths = sum(len(d.get('rules', [])) + (1 if d.get('defaultConnector') else 0) 
                         for d in decisions)
        
        return total_paths / len(decisions)
    
    def _find_hardcoded_values(self, flow_data: Dict) -> List[Dict]:
        """Find hardcoded values that should be variables"""
        metadata = flow_data.get('Metadata', {})
        hardcoded = []
        
        for create in metadata.get('recordCreates', []):
            for assign in create.get('inputAssignments', []):
                value = assign.get('value', {})
                if isinstance(value, dict):
                    str_val = value.get('stringValue', '')
                    if str_val and not str_val.startswith('{'):
                        hardcoded.append({
                            'element': create.get('name'),
                            'field': assign.get('field'),
                            'value': str_val
                        })
        
        return hardcoded
    
    def _find_missing_faults(self, flow_data: Dict) -> List[str]:
        """Find elements missing fault handling"""
        metadata = flow_data.get('Metadata', {})
        missing = []
        
        for action in metadata.get('actionCalls', []):
            if action.get('actionType') == 'apex' and not action.get('faultConnector'):
                missing.append(action.get('name'))
        
        return missing
    
    def _extract_value(self, value_obj: Any) -> Any:
        """Extract value from Salesforce value object"""
        if not isinstance(value_obj, dict):
            return value_obj
        
        return (value_obj.get('stringValue') or 
                value_obj.get('booleanValue') or 
                value_obj.get('numberValue') or 
                value_obj.get('elementReference') or
                '')


# =============================================================================
# PATTERN LEARNER
# =============================================================================

class FlowPatternLearner:
    """Learns patterns from flow data"""
    
    def __init__(self):
        self.patterns: Dict[str, FlowPattern] = {}
        self.decision_patterns: Dict[str, int] = defaultdict(int)
        self.trigger_patterns: Dict[str, int] = defaultdict(int)
        self.object_patterns: Dict[str, int] = defaultdict(int)
        self.structure_patterns: Dict[str, int] = defaultdict(int)
    
    def learn(self, flows: List[Dict]):
        """Learn patterns from a list of flows"""
        for flow in flows:
            self._learn_from_flow(flow)
        
        self._consolidate_patterns()
    
    def _learn_from_flow(self, flow_data: Dict):
        """Learn patterns from a single flow"""
        metadata = flow_data.get('Metadata', {})
        
        # Learn decision patterns
        for decision in metadata.get('decisions') or []:
            if not decision:
                continue
            for rule in decision.get('rules') or []:
                if not rule:
                    continue
                for cond in rule.get('conditions') or []:
                    if not cond:
                        continue
                    pattern = f"{cond.get('operator', '')}_{cond.get('leftValueReference', '').split('.')[-1] if '.' in str(cond.get('leftValueReference', '')) else 'field'}"
                    self.decision_patterns[pattern] += 1
        
        # Learn trigger patterns
        start = metadata.get('start') or {}
        if start and start.get('triggerType'):
            pattern = f"{start.get('triggerType')}_{start.get('object', 'Unknown')}"
            self.trigger_patterns[pattern] += 1
        
        # Learn object usage patterns
        for obj in self._get_objects(flow_data):
            self.object_patterns[obj] += 1
        
        # Learn structural patterns
        structure = self._get_structure_pattern(flow_data)
        self.structure_patterns[structure] += 1
    
    def _get_objects(self, flow_data: Dict) -> List[str]:
        """Get all objects from flow"""
        objects = []
        metadata = flow_data.get('Metadata', {})
        if not metadata:
            return objects
        
        start = metadata.get('start') or {}
        if start and start.get('object'):
            objects.append(start['object'])
        
        for lookup in metadata.get('recordLookups') or []:
            if lookup and lookup.get('object'):
                objects.append(lookup['object'])
        
        return objects
    
    def _get_structure_pattern(self, flow_data: Dict) -> str:
        """Get structural pattern of flow"""
        metadata = flow_data.get('Metadata', {})
        if not metadata:
            return 'EMPTY'
        
        parts = []
        start = metadata.get('start') or {}
        if start and start.get('triggerType'):
            parts.append('T')  # Triggered
        if metadata.get('decisions'):
            parts.append(f'D{len(metadata["decisions"])}')
        if metadata.get('recordLookups'):
            parts.append(f'L{len(metadata["recordLookups"])}')
        if metadata.get('recordCreates'):
            parts.append(f'C{len(metadata["recordCreates"])}')
        if metadata.get('recordUpdates'):
            parts.append(f'U{len(metadata["recordUpdates"])}')
        if metadata.get('screens'):
            parts.append(f'S{len(metadata["screens"])}')
        
        return '_'.join(parts) or 'EMPTY'
    
    def _consolidate_patterns(self):
        """Consolidate learned patterns"""
        # Decision patterns
        for pattern, freq in self.decision_patterns.items():
            self.patterns[f"decision_{pattern}"] = FlowPattern(
                pattern_id=f"decision_{pattern}",
                pattern_type="decision",
                frequency=freq,
                confidence=freq / max(sum(self.decision_patterns.values()), 1)
            )
        
        # Trigger patterns
        for pattern, freq in self.trigger_patterns.items():
            self.patterns[f"trigger_{pattern}"] = FlowPattern(
                pattern_id=f"trigger_{pattern}",
                pattern_type="trigger",
                frequency=freq,
                confidence=freq / max(sum(self.trigger_patterns.values()), 1)
            )
    
    def get_similar_patterns(self, flow_data: Dict) -> List[FlowPattern]:
        """Get patterns similar to a flow"""
        similar = []
        structure = self._get_structure_pattern(flow_data)
        
        for pattern_id, pattern in self.patterns.items():
            if structure in pattern_id or pattern.pattern_type in structure.lower():
                similar.append(pattern)
        
        return sorted(similar, key=lambda p: p.confidence, reverse=True)


# =============================================================================
# SCENARIO GENERATOR (ML-based)
# =============================================================================

class MLScenarioGenerator:
    """ML-based test scenario generator"""
    
    SCENARIO_TEMPLATES = {
        "decision_logic": {
            "template": "In '{flow_name}', explain the decision '{decision_name}' - when does the '{rule_name}' path execute?",
            "category": "Decision Logic Analysis"
        },
        "null_handling": {
            "template": "How does '{flow_name}' handle null values for {variable}? What path does the flow take?",
            "category": "Null Value Handling"
        },
        "trigger_condition": {
            "template": "When does '{flow_name}' get triggered? What condition on {field} must be met?",
            "category": "Flow Trigger Conditions"
        },
        "record_create": {
            "template": "In '{flow_name}', what {object} record is created? What fields are set?",
            "category": "Record Creation Analysis"
        },
        "record_update": {
            "template": "In '{flow_name}', what changes does '{element_name}' make to the record?",
            "category": "Record Update Analysis"
        },
        "default_path": {
            "template": "In '{flow_name}', what happens if NONE of the conditions in '{decision_name}' are met?",
            "category": "Default Path Analysis"
        },
        "apex_fault": {
            "template": "What happens in '{flow_name}' if the Apex action '{apex_name}' fails?",
            "category": "Apex Fault Handling"
        },
        "screen_validation": {
            "template": "In '{flow_name}', what are the required fields on the '{screen_name}' screen?",
            "category": "Screen Validation Analysis"
        }
    }
    
    def __init__(self, feature_extractor: FlowFeatureExtractor):
        self.feature_extractor = feature_extractor
        self.generated_count = 0
    
    def generate(self, flow_data: Dict) -> List[Dict]:
        """Generate test scenarios for a flow"""
        features = self.feature_extractor.extract(flow_data)
        scenarios = []
        
        flow_name = flow_data.get('MasterLabel') or flow_data.get('FullName', 'Unknown')
        dev_name = flow_data.get('FullName', '')
        
        # Generate decision scenarios
        for decision in features['decisions']:
            scenarios.extend(self._generate_decision_scenarios(flow_name, dev_name, decision))
        
        # Generate trigger scenarios
        if features['triggers']['type']:
            scenarios.extend(self._generate_trigger_scenarios(flow_name, dev_name, features['triggers']))
        
        # Generate record operation scenarios
        for op in features['record_operations']:
            scenarios.extend(self._generate_record_scenarios(flow_name, dev_name, op))
        
        # Generate screen scenarios
        for screen in features['screens']:
            scenarios.extend(self._generate_screen_scenarios(flow_name, dev_name, screen))
        
        # Generate apex scenarios
        for apex in features['apex_calls']:
            scenarios.extend(self._generate_apex_scenarios(flow_name, dev_name, apex))
        
        return scenarios
    
    def _generate_decision_scenarios(self, flow_name: str, dev_name: str, decision: Dict) -> List[Dict]:
        """Generate scenarios for a decision"""
        scenarios = []
        
        for rule in decision.get('rules', []):
            # Decision logic scenario
            self.generated_count += 1
            conditions_str = ' and '.join(
                f"{c['left']} {c['operator']} {c['right']}" 
                for c in rule.get('conditions', [])
            )
            
            scenarios.append({
                'id': f"decision_{decision['name']}_{rule['name']}",
                'category': 'Decision Logic Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', explain the decision '{decision.get('label', decision['name'])}' - when does the '{rule.get('label', rule['name'])}' path execute?",
                'context': f"Conditions: {conditions_str}",
                'expected_analysis': [f"{c['left']} {c['operator']} {c['right']}" for c in rule.get('conditions', [])]
            })
            
            # Null handling scenarios
            for cond in rule.get('conditions', []):
                if cond['operator'] == 'IsNull':
                    scenarios.append({
                        'id': f"null_{decision['name']}_{rule['name']}",
                        'category': 'Null Value Handling',
                        'flow': dev_name,
                        'query': f"How does '{flow_name}' handle null values for {cond['left']}?",
                        'context': f"Null check: {cond['left']} IsNull = {cond['right']}",
                        'expected_analysis': [f"Checks if {cond['left']} is null", f"Expected null state: {cond['right']}"]
                    })
        
        # Default path scenario
        if decision.get('has_default'):
            scenarios.append({
                'id': f"default_{decision['name']}",
                'category': 'Default Path Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', what is the default outcome if NONE of the conditions in '{decision.get('label', decision['name'])}' are met?",
                'context': f"Analyzing default connector for decision: {decision.get('label', decision['name'])}",
                'expected_analysis': ['Default path behavior', 'Fallback logic']
            })
        
        return scenarios
    
    def _generate_trigger_scenarios(self, flow_name: str, dev_name: str, trigger: Dict) -> List[Dict]:
        """Generate scenarios for triggers"""
        scenarios = []
        
        for i, cond in enumerate(trigger.get('conditions', [])):
            scenarios.append({
                'id': f"trigger_{i+1}",
                'category': 'Flow Trigger Conditions',
                'flow': dev_name,
                'query': f"When does '{flow_name}' get triggered? What condition on {cond['field']} must be met?",
                'context': f"Trigger: {cond['field']} {cond['operator']} {cond['value']}",
                'expected_analysis': [f"Field: {cond['field']}", f"Operator: {cond['operator']}", f"Value: {cond['value']}"]
            })
            
            # Edge case scenario
            scenarios.append({
                'id': f"trigger_edge_{i+1}",
                'category': 'Flow Trigger Edge Cases',
                'flow': dev_name,
                'query': f"What happens in '{flow_name}' if {cond['field']} does NOT meet the condition '{cond['operator']} {cond['value']}'?",
                'context': f"Testing trigger condition: {cond['field']} {cond['operator']} {cond['value']}",
                'expected_analysis': ['Flow will NOT execute', f"Requires {cond['field']} condition to be met"]
            })
        
        return scenarios
    
    def _generate_record_scenarios(self, flow_name: str, dev_name: str, op: Dict) -> List[Dict]:
        """Generate scenarios for record operations"""
        scenarios = []
        
        if op['type'] == 'create':
            scenarios.append({
                'id': f"create_{op['name']}",
                'category': 'Record Creation Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', what {op['object']} record is created by '{op['name']}'?",
                'context': f"Object: {op['object']}, Fields: {op.get('fields', 0)}",
                'expected_analysis': [f"Creates {op['object']} record", f"Sets {op.get('fields', 'multiple')} fields"]
            })
        
        elif op['type'] == 'update':
            scenarios.append({
                'id': f"update_{op['name']}",
                'category': 'Record Update Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', what changes does '{op['name']}' make to the record?",
                'context': f"Object: {op['object']}, Updates: {op.get('fields', 0)} fields",
                'expected_analysis': [f"Updates {op['object']}", f"Modifies {op.get('fields', 'multiple')} fields"]
            })
        
        elif op['type'] == 'lookup':
            scenarios.append({
                'id': f"lookup_{op['name']}",
                'category': 'Record Lookup Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', how does '{op['name']}' query {op['object']} records?",
                'context': f"Object: {op['object']}, Filters: {op.get('filters', 0)}",
                'expected_analysis': [f"Queries {op['object']}", f"Applies {op.get('filters', 0)} filters"]
            })
            
            # Empty result scenario
            scenarios.append({
                'id': f"lookup_empty_{op['name']}",
                'category': 'Empty Result Handling',
                'flow': dev_name,
                'query': f"What happens in '{flow_name}' if '{op['name']}' returns NO records?",
                'context': f"Analyzing null/empty handling for {op['object']} query",
                'expected_analysis': ['Null assignment handling', 'Downstream decision impact']
            })
        
        return scenarios
    
    def _generate_screen_scenarios(self, flow_name: str, dev_name: str, screen: Dict) -> List[Dict]:
        """Generate scenarios for screens"""
        scenarios = []
        
        if screen.get('required_count', 0) > 0:
            required_fields = [f['name'] for f in screen.get('fields', []) if f.get('required')]
            scenarios.append({
                'id': f"screen_{screen['name']}_validation",
                'category': 'Screen Validation Analysis',
                'flow': dev_name,
                'query': f"In '{flow_name}', what are the required fields on the '{screen.get('label', screen['name'])}' screen?",
                'context': f"Screen: {screen.get('label', screen['name'])}, Required fields: {screen['required_count']}",
                'expected_analysis': [f"{f} (required)" for f in required_fields]
            })
        
        return scenarios
    
    def _generate_apex_scenarios(self, flow_name: str, dev_name: str, apex: Dict) -> List[Dict]:
        """Generate scenarios for Apex calls"""
        scenarios = []
        
        scenarios.append({
            'id': f"apex_{apex['name']}",
            'category': 'Apex Integration Analysis',
            'flow': dev_name,
            'query': f"In '{flow_name}', what does the Apex action '{apex['action_name']}' do?",
            'context': f"Apex class: {apex['action_name']}",
            'expected_analysis': [f"Action: {apex['action_name']}", 'Input/output mapping']
        })
        
        if not apex.get('has_fault_path'):
            scenarios.append({
                'id': f"apex_fault_{apex['name']}",
                'category': 'Apex Fault Handling',
                'flow': dev_name,
                'query': f"What happens in '{flow_name}' if the Apex callout '{apex['action_name']}' fails?",
                'context': f"Analyzing fault connector for {apex['action_name']}",
                'expected_analysis': ['Fault handling path', 'Error recovery']
            })
        
        return scenarios


# =============================================================================
# QUERY UNDERSTANDING (NLU)
# =============================================================================

class FlowQueryUnderstanding:
    """Natural Language Understanding for flow queries"""
    
    INTENT_PATTERNS = {
        'trigger': [
            r'when.*trigger', r'what.*trigger', r'trigger.*condition',
            r'fires when', r'executed when', r'runs when'
        ],
        'decision': [
            r'decision', r'condition', r'branch', r'path.*take',
            r'what happens.*if', r'when does.*path'
        ],
        'record_operation': [
            r'create.*record', r'update.*record', r'lookup.*record',
            r'what.*create', r'what.*update', r'fields.*set'
        ],
        'error_handling': [
            r'error', r'fail', r'fault', r'exception', r'handle.*error'
        ],
        'explanation': [
            r'explain', r'what does.*do', r'how does.*work',
            r'describe', r'summary'
        ],
        'validation': [
            r'required', r'validation', r'mandatory', r'must.*provide'
        ]
    }
    
    def __init__(self):
        self.compiled_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.INTENT_PATTERNS.items()
        }
    
    def understand(self, query: str) -> Dict[str, Any]:
        """Understand a natural language query"""
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Determine confidence
        confidence = self._calculate_confidence(intent, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'original_query': query
        }
    
    def _detect_intent(self, query: str) -> str:
        """Detect the intent of a query"""
        scores = {}
        
        for intent, patterns in self.compiled_patterns.items():
            score = sum(1 for p in patterns if p.search(query))
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return 'general'
        
        return max(scores, key=scores.get)
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query"""
        entities = {
            'flow_names': [],
            'field_names': [],
            'object_names': [],
            'element_names': []
        }
        
        # Extract quoted strings as potential names
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", query)
        for match in quoted:
            name = match[0] or match[1]
            entities['element_names'].append(name)
        
        # Extract potential object names (capitalized words ending with __c or standard objects)
        objects = re.findall(r'\b([A-Z][a-z]+(?:__c)?)\b', query)
        entities['object_names'] = list(set(objects))
        
        # Extract potential field names (words with __c or containing underscores)
        fields = re.findall(r'\b(\w+__c|\w+_\w+)\b', query, re.IGNORECASE)
        entities['field_names'] = list(set(fields))
        
        return entities
    
    def _calculate_confidence(self, intent: str, entities: Dict) -> float:
        """Calculate confidence in understanding"""
        base_confidence = 0.5 if intent == 'general' else 0.7
        
        # Boost confidence if entities found
        entity_count = sum(len(v) for v in entities.values())
        if entity_count > 0:
            base_confidence += min(0.2, entity_count * 0.05)
        
        return min(1.0, base_confidence)


# =============================================================================
# MAIN AI/ML MODEL
# =============================================================================

class SalesforceFlowAIModel:
    """
    Main AI/ML Model for Salesforce Flow Analysis
    
    This model combines:
    - Feature extraction
    - Pattern learning
    - Scenario generation
    - Query understanding
    - LLM integration for complex reasoning
    
    Usage:
        model = SalesforceFlowAIModel()
        model.train(flows_data)
        
        # Analyze a flow
        result = model.predict(flow_data, task=ModelTask.FLOW_ANALYSIS)
        
        # Answer a question
        answer = model.query("What triggers this flow?", flow_data)
        
        # Generate scenarios
        scenarios = model.generate_scenarios(flow_data)
    """
    
    VERSION = "2.0.0"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_llm: bool = True,
        llm_provider: str = "github"
    ):
        """
        Initialize the AI/ML Model
        
        Args:
            model_path: Path to load pre-trained model
            use_llm: Whether to use LLM for complex reasoning
            llm_provider: LLM provider (github, openai, azure, anthropic)
        """
        # Core components
        self.feature_extractor = FlowFeatureExtractor()
        self.pattern_learner = FlowPatternLearner()
        self.scenario_generator = MLScenarioGenerator(self.feature_extractor)
        self.query_understanding = FlowQueryUnderstanding()
        
        # Model state
        self.is_trained = False
        self.training_flows: List[Dict] = []
        self.metrics = ModelMetrics()
        
        # LLM integration
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self._llm = None
        
        # Load pre-trained model if provided
        if model_path and os.path.exists(model_path):
            self.load(model_path)
    
    @property
    def llm(self):
        """Lazy-load LLM"""
        if self._llm is None and self.use_llm:
            try:
                from src.model import create_model_from_config
                self._llm = create_model_from_config()
            except Exception as e:
                print(f"Warning: Could not load LLM: {e}")
                self._llm = None
        return self._llm
    
    # =========================================================================
    # TRAINING
    # =========================================================================
    
    def train(
        self,
        flows: List[Dict],
        epochs: int = 1,
        verbose: bool = True
    ) -> ModelMetrics:
        """
        Train the model on flow data
        
        Args:
            flows: List of flow metadata dictionaries
            epochs: Number of training epochs
            verbose: Print training progress
            
        Returns:
            Training metrics
        """
        if verbose:
            print(f"🎯 Training SalesforceFlowAIModel v{self.VERSION}")
            print(f"   Flows: {len(flows)}")
            print(f"   Epochs: {epochs}")
        
        self.training_flows = flows
        
        for epoch in range(epochs):
            if verbose:
                print(f"\n📚 Epoch {epoch + 1}/{epochs}")
            
            # Extract features from all flows
            for i, flow in enumerate(flows):
                features = self.feature_extractor.extract(flow)
                if verbose and (i + 1) % 5 == 0:
                    print(f"   Processed {i + 1}/{len(flows)} flows")
            
            # Learn patterns
            self.pattern_learner.learn(flows)
            
            if verbose:
                print(f"   Learned {len(self.pattern_learner.patterns)} patterns")
        
        self.is_trained = True
        
        # Calculate metrics
        self.metrics = self._calculate_training_metrics()
        
        if verbose:
            print(f"\n✅ Training complete!")
            print(f"   Patterns learned: {len(self.pattern_learner.patterns)}")
            print(f"   Decision patterns: {len(self.pattern_learner.decision_patterns)}")
            print(f"   Trigger patterns: {len(self.pattern_learner.trigger_patterns)}")
        
        return self.metrics
    
    def _calculate_training_metrics(self) -> ModelMetrics:
        """Calculate training metrics"""
        metrics = ModelMetrics()
        metrics.total_predictions = len(self.training_flows)
        
        # Calculate pattern coverage
        covered = sum(1 for f in self.training_flows 
                     if self.pattern_learner.get_similar_patterns(f))
        metrics.accuracy = covered / max(len(self.training_flows), 1)
        
        return metrics
    
    # =========================================================================
    # PREDICTION / INFERENCE
    # =========================================================================
    
    def predict(
        self,
        flow_data: Dict,
        task: ModelTask = ModelTask.FLOW_ANALYSIS
    ) -> ModelPrediction:
        """
        Make a prediction for a given task
        
        Args:
            flow_data: Flow metadata dictionary
            task: Type of prediction to make
            
        Returns:
            ModelPrediction with results
        """
        handlers = {
            ModelTask.FLOW_ANALYSIS: self._predict_analysis,
            ModelTask.DECISION_EXTRACTION: self._predict_decisions,
            ModelTask.TRIGGER_ANALYSIS: self._predict_triggers,
            ModelTask.SCENARIO_GENERATION: self._predict_scenarios,
            ModelTask.BEST_PRACTICE_CHECK: self._predict_best_practices,
            ModelTask.ANOMALY_DETECTION: self._predict_anomalies,
            ModelTask.IMPACT_PREDICTION: self._predict_impact,
        }
        
        handler = handlers.get(task, self._predict_analysis)
        return handler(flow_data)
    
    def _predict_analysis(self, flow_data: Dict) -> ModelPrediction:
        """Full flow analysis prediction"""
        features = self.feature_extractor.extract(flow_data)
        similar_patterns = self.pattern_learner.get_similar_patterns(flow_data)
        
        return ModelPrediction(
            task=ModelTask.FLOW_ANALYSIS,
            prediction={
                'flow_type': features['flow_type'],
                'complexity': features['complexity_score'],
                'elements': features['element_count'],
                'decisions': len(features['decisions']),
                'record_operations': len(features['record_operations']),
                'triggers': features['triggers'],
                'similar_patterns': [p.pattern_id for p in similar_patterns[:5]]
            },
            confidence=0.9 if self.is_trained else 0.7,
            reasoning=[
                f"Flow type: {features['flow_type']}",
                f"Complexity score: {features['complexity_score']:.1f}/100",
                f"Found {len(features['decisions'])} decisions",
                f"Found {len(features['record_operations'])} record operations"
            ]
        )
    
    def _predict_decisions(self, flow_data: Dict) -> ModelPrediction:
        """Extract and analyze decisions"""
        features = self.feature_extractor.extract(flow_data)
        decisions = features['decisions']
        
        analysis = []
        for dec in decisions:
            analysis.append({
                'name': dec['name'],
                'label': dec['label'],
                'rules_count': len(dec['rules']),
                'has_default': dec['has_default'],
                'conditions': sum(len(r['conditions']) for r in dec['rules'])
            })
        
        return ModelPrediction(
            task=ModelTask.DECISION_EXTRACTION,
            prediction=analysis,
            confidence=0.95,
            reasoning=[f"Extracted {len(decisions)} decisions with {sum(d['rules_count'] for d in analysis)} total rules"]
        )
    
    def _predict_triggers(self, flow_data: Dict) -> ModelPrediction:
        """Analyze trigger configuration"""
        features = self.feature_extractor.extract(flow_data)
        triggers = features['triggers']
        
        return ModelPrediction(
            task=ModelTask.TRIGGER_ANALYSIS,
            prediction=triggers,
            confidence=0.95 if triggers['type'] else 0.5,
            reasoning=[
                f"Trigger type: {triggers['type'] or 'None (Screen Flow)'}",
                f"Object: {triggers['object'] or 'N/A'}",
                f"Conditions: {len(triggers['conditions'])}"
            ]
        )
    
    def _predict_scenarios(self, flow_data: Dict) -> ModelPrediction:
        """Generate test scenarios"""
        scenarios = self.scenario_generator.generate(flow_data)
        
        # Group by category
        by_category = defaultdict(list)
        for s in scenarios:
            by_category[s['category']].append(s)
        
        return ModelPrediction(
            task=ModelTask.SCENARIO_GENERATION,
            prediction=scenarios,
            confidence=0.85,
            reasoning=[
                f"Generated {len(scenarios)} scenarios",
                f"Categories: {len(by_category)}",
                *[f"  - {cat}: {len(items)}" for cat, items in by_category.items()]
            ],
            metadata={'by_category': dict(by_category)}
        )
    
    def _predict_best_practices(self, flow_data: Dict) -> ModelPrediction:
        """Check best practices"""
        features = self.feature_extractor.extract(flow_data)
        issues = []
        
        # Check for null handling
        if not features['has_null_checks'] and features['decisions']:
            issues.append({
                'severity': Severity.WARNING.value,
                'category': 'Null Handling',
                'message': 'Flow has decisions but no null checks',
                'recommendation': 'Add IsNull checks before comparisons'
            })
        
        # Check for error handling
        if features['apex_calls'] and not features['has_error_handling']:
            issues.append({
                'severity': Severity.WARNING.value,
                'category': 'Error Handling',
                'message': 'Apex calls without fault handling',
                'recommendation': 'Add fault connectors to Apex actions'
            })
        
        # Check for hardcoded values
        for hardcoded in features['hardcoded_values'][:5]:  # Limit to 5
            issues.append({
                'severity': Severity.INFO.value,
                'category': 'Maintainability',
                'message': f"Hardcoded value '{hardcoded['value']}' in {hardcoded['element']}",
                'recommendation': 'Consider using variables or custom metadata'
            })
        
        # Check complexity
        if features['complexity_score'] > 70:
            issues.append({
                'severity': Severity.WARNING.value,
                'category': 'Complexity',
                'message': f"High complexity score: {features['complexity_score']:.1f}",
                'recommendation': 'Consider breaking into subflows'
            })
        
        return ModelPrediction(
            task=ModelTask.BEST_PRACTICE_CHECK,
            prediction=issues,
            confidence=0.8,
            reasoning=[f"Found {len(issues)} potential issues"]
        )
    
    def _predict_anomalies(self, flow_data: Dict) -> ModelPrediction:
        """Detect anomalies based on learned patterns"""
        if not self.is_trained:
            return ModelPrediction(
                task=ModelTask.ANOMALY_DETECTION,
                prediction=[],
                confidence=0.3,
                reasoning=["Model not trained - cannot detect anomalies"]
            )
        
        features = self.feature_extractor.extract(flow_data)
        anomalies = []
        
        # Check if complexity is unusual
        avg_complexity = sum(
            self.feature_extractor.extract(f)['complexity_score']
            for f in self.training_flows
        ) / max(len(self.training_flows), 1)
        
        if abs(features['complexity_score'] - avg_complexity) > 30:
            anomalies.append({
                'type': 'complexity',
                'message': f"Unusual complexity: {features['complexity_score']:.1f} (avg: {avg_complexity:.1f})",
                'severity': 'info'
            })
        
        # Check for unusual patterns
        similar = self.pattern_learner.get_similar_patterns(flow_data)
        if not similar:
            anomalies.append({
                'type': 'pattern',
                'message': 'No similar patterns found in training data',
                'severity': 'warning'
            })
        
        return ModelPrediction(
            task=ModelTask.ANOMALY_DETECTION,
            prediction=anomalies,
            confidence=0.7 if self.is_trained else 0.3,
            reasoning=[f"Detected {len(anomalies)} potential anomalies"]
        )
    
    def _predict_impact(self, flow_data: Dict) -> ModelPrediction:
        """Predict impact of changes"""
        features = self.feature_extractor.extract(flow_data)
        
        impact = {
            'objects_affected': features['objects_used'],
            'record_operations': len(features['record_operations']),
            'has_external_calls': len(features['apex_calls']) > 0,
            'triggers_on': features['triggers']['object'],
            'risk_level': 'low'
        }
        
        # Calculate risk level
        if features['complexity_score'] > 50 or len(features['apex_calls']) > 0:
            impact['risk_level'] = 'medium'
        if features['complexity_score'] > 70 and not features['has_error_handling']:
            impact['risk_level'] = 'high'
        
        return ModelPrediction(
            task=ModelTask.IMPACT_PREDICTION,
            prediction=impact,
            confidence=0.75,
            reasoning=[
                f"Affects {len(impact['objects_affected'])} objects",
                f"Risk level: {impact['risk_level']}"
            ]
        )
    
    # =========================================================================
    # QUERY / CHAT
    # =========================================================================
    
    def query(
        self,
        question: str,
        flow_data: Optional[Dict] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a natural language question about a flow
        
        Args:
            question: Natural language question
            flow_data: Optional flow to query about
            use_llm: Whether to use LLM for response
            
        Returns:
            Dictionary with answer and metadata
        """
        # Understand the query
        understanding = self.query_understanding.understand(question)
        
        # If we have flow data, extract features
        context = {}
        if flow_data:
            context['features'] = self.feature_extractor.extract(flow_data)
            context['flow_name'] = flow_data.get('MasterLabel', flow_data.get('FullName', 'Unknown'))
        
        # Try rule-based response first
        rule_response = self._rule_based_response(understanding, context)
        
        # If LLM available and enabled, enhance with LLM
        if use_llm and self.use_llm and self.llm:
            try:
                llm_response = self.llm.query(question, flow_metadata=flow_data)
                return {
                    'answer': llm_response,
                    'source': 'llm',
                    'intent': understanding['intent'],
                    'confidence': understanding['confidence'],
                    'rule_based_hint': rule_response
                }
            except Exception as e:
                pass  # Fall back to rule-based
        
        return {
            'answer': rule_response,
            'source': 'rule_based',
            'intent': understanding['intent'],
            'confidence': understanding['confidence']
        }
    
    def _rule_based_response(self, understanding: Dict, context: Dict) -> str:
        """Generate rule-based response"""
        intent = understanding['intent']
        features = context.get('features', {})
        flow_name = context.get('flow_name', 'this flow')
        
        if intent == 'trigger':
            triggers = features.get('triggers', {})
            if triggers.get('type'):
                conditions = ', '.join(
                    f"{c['field']} {c['operator']} {c['value']}"
                    for c in triggers.get('conditions', [])
                )
                return f"{flow_name} triggers on {triggers['object']} when: {conditions or 'record is created/updated'}"
            return f"{flow_name} is a Screen Flow (no automatic trigger)"
        
        elif intent == 'decision':
            decisions = features.get('decisions', [])
            if decisions:
                dec_summary = ', '.join(d['label'] or d['name'] for d in decisions[:3])
                return f"{flow_name} has {len(decisions)} decisions: {dec_summary}"
            return f"{flow_name} has no decision elements"
        
        elif intent == 'record_operation':
            ops = features.get('record_operations', [])
            if ops:
                summary = ', '.join(f"{o['type']} {o['object']}" for o in ops[:3])
                return f"{flow_name} performs {len(ops)} record operations: {summary}"
            return f"{flow_name} has no record operations"
        
        elif intent == 'error_handling':
            if features.get('has_error_handling'):
                return f"{flow_name} has error handling configured"
            return f"{flow_name} does NOT have explicit error handling. Consider adding fault connectors."
        
        elif intent == 'explanation':
            flow_type = features.get('flow_type', 'Unknown')
            complexity = features.get('complexity_score', 0)
            return f"{flow_name} is a {flow_type} flow with complexity {complexity:.0f}/100"
        
        return f"I understand you're asking about {intent}. Please provide more specific details."
    
    # =========================================================================
    # SCENARIO GENERATION
    # =========================================================================
    
    def generate_scenarios(
        self,
        flow_data: Optional[Dict] = None,
        flows: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate test scenarios for one or more flows
        
        Args:
            flow_data: Single flow to generate scenarios for
            flows: Multiple flows to generate scenarios for
            
        Returns:
            List of scenario dictionaries
        """
        all_scenarios = []
        
        if flow_data:
            all_scenarios.extend(self.scenario_generator.generate(flow_data))
        
        if flows:
            for flow in flows:
                all_scenarios.extend(self.scenario_generator.generate(flow))
        
        return all_scenarios
    
    # =========================================================================
    # MODEL PERSISTENCE
    # =========================================================================
    
    def save(self, path: str):
        """Save model to disk"""
        model_state = {
            'version': self.VERSION,
            'is_trained': self.is_trained,
            'patterns': {k: asdict(v) for k, v in self.pattern_learner.patterns.items()},
            'decision_patterns': dict(self.pattern_learner.decision_patterns),
            'trigger_patterns': dict(self.pattern_learner.trigger_patterns),
            'metrics': asdict(self.metrics),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_state, f)
        
        print(f"✅ Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            model_state = pickle.load(f)
        
        self.is_trained = model_state['is_trained']
        self.pattern_learner.patterns = {
            k: FlowPattern(**v) for k, v in model_state['patterns'].items()
        }
        self.pattern_learner.decision_patterns = defaultdict(int, model_state['decision_patterns'])
        self.pattern_learner.trigger_patterns = defaultdict(int, model_state['trigger_patterns'])
        self.metrics = ModelMetrics(**model_state['metrics'])
        
        print(f"✅ Model loaded from {path} (v{model_state['version']})")
    
    def export_onnx(self, path: str):
        """Export model patterns to JSON (ONNX-like portable format)"""
        export_data = {
            'model_name': 'SalesforceFlowAIModel',
            'version': self.VERSION,
            'exported_at': datetime.now().isoformat(),
            'patterns': {k: asdict(v) for k, v in self.pattern_learner.patterns.items()},
            'feature_names': list(self.feature_extractor.feature_cache.keys())[:10],
            'supported_tasks': [t.value for t in ModelTask]
        }
        
        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Model exported to {path}")
    
    # =========================================================================
    # EVALUATION
    # =========================================================================
    
    def evaluate(
        self,
        test_flows: List[Dict],
        test_scenarios: Optional[List[Dict]] = None
    ) -> ModelMetrics:
        """
        Evaluate model performance
        
        Args:
            test_flows: Flows to evaluate on
            test_scenarios: Optional scenarios with expected results
            
        Returns:
            Evaluation metrics
        """
        metrics = ModelMetrics()
        
        # Evaluate feature extraction
        for flow in test_flows:
            try:
                features = self.feature_extractor.extract(flow)
                metrics.total_predictions += 1
                if features:
                    metrics.correct_predictions += 1
            except Exception:
                pass
        
        metrics.accuracy = metrics.correct_predictions / max(metrics.total_predictions, 1)
        
        # Evaluate scenario generation if provided
        if test_scenarios:
            scenario_correct = 0
            for scenario in test_scenarios:
                flow_name = scenario.get('flow')
                matching_flow = next(
                    (f for f in test_flows if f.get('FullName') == flow_name),
                    None
                )
                if matching_flow:
                    generated = self.generate_scenarios(matching_flow)
                    if any(s['category'] == scenario['category'] for s in generated):
                        scenario_correct += 1
            
            metrics.task_metrics['scenario_generation'] = {
                'accuracy': scenario_correct / max(len(test_scenarios), 1)
            }
        
        return metrics
    
    # =========================================================================
    # CLI
    # =========================================================================
    
    @classmethod
    def cli(cls):
        """Command-line interface"""
        import argparse
        
        parser = argparse.ArgumentParser(description="Salesforce Flow AI/ML Model")
        subparsers = parser.add_subparsers(dest="command")
        
        # Train command
        train_parser = subparsers.add_parser("train", help="Train the model")
        train_parser.add_argument("--flows-dir", default="org_flows", help="Directory with flow JSON files")
        train_parser.add_argument("--output", default="flow_model.pkl", help="Output model file")
        train_parser.add_argument("--epochs", type=int, default=1, help="Training epochs")
        
        # Predict command
        predict_parser = subparsers.add_parser("predict", help="Make predictions")
        predict_parser.add_argument("--flow", required=True, help="Flow file to analyze")
        predict_parser.add_argument("--task", default="flow_analysis", help="Task to perform")
        predict_parser.add_argument("--model", default="flow_model.pkl", help="Model file")
        
        # Query command
        query_parser = subparsers.add_parser("query", help="Ask a question")
        query_parser.add_argument("question", help="Question to ask")
        query_parser.add_argument("--flow", help="Optional flow context")
        query_parser.add_argument("--model", default="flow_model.pkl", help="Model file")
        
        # Generate command
        gen_parser = subparsers.add_parser("generate", help="Generate scenarios")
        gen_parser.add_argument("--flows-dir", default="org_flows", help="Directory with flows")
        gen_parser.add_argument("--output", default="generated_scenarios.json", help="Output file")
        
        # Export command
        export_parser = subparsers.add_parser("export", help="Export model")
        export_parser.add_argument("--model", default="flow_model.pkl", help="Model file")
        export_parser.add_argument("--output", default="flow_model.json", help="Output file")
        
        args = parser.parse_args()
        
        if args.command == "train":
            model = cls(use_llm=False)
            
            # Load flows
            flows = []
            flows_dir = Path(args.flows_dir)
            for flow_file in flows_dir.glob("*.json"):
                if flow_file.name.startswith("_"):
                    continue
                with open(flow_file) as f:
                    flows.append(json.load(f))
            
            # Train
            metrics = model.train(flows, epochs=args.epochs)
            
            # Save
            model.save(args.output)
            print(f"\nMetrics: Accuracy={metrics.accuracy:.2%}")
        
        elif args.command == "predict":
            model = cls(use_llm=False)
            if os.path.exists(args.model):
                model.load(args.model)
            
            with open(args.flow) as f:
                flow_data = json.load(f)
            
            task = ModelTask(args.task)
            result = model.predict(flow_data, task=task)
            
            print(f"\n📊 Prediction ({task.value}):")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Reasoning:")
            for r in result.reasoning:
                print(f"     - {r}")
            print(f"\n   Result: {json.dumps(result.prediction, indent=2)}")
        
        elif args.command == "query":
            model = cls(use_llm=True)
            if os.path.exists(args.model):
                model.load(args.model)
            
            flow_data = None
            if args.flow:
                with open(args.flow) as f:
                    flow_data = json.load(f)
            
            result = model.query(args.question, flow_data)
            print(f"\n💬 Answer ({result['source']}):")
            print(f"   Intent: {result['intent']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"\n   {result['answer']}")
        
        elif args.command == "generate":
            model = cls(use_llm=False)
            
            # Load flows
            flows = []
            flows_dir = Path(args.flows_dir)
            for flow_file in flows_dir.glob("*.json"):
                if flow_file.name.startswith("_"):
                    continue
                with open(flow_file) as f:
                    flows.append(json.load(f))
            
            # Generate scenarios
            scenarios = model.generate_scenarios(flows=flows)
            
            # Save
            output = {
                'generated_at': datetime.now().isoformat(),
                'total_scenarios': len(scenarios),
                'scenarios': scenarios
            }
            
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"✅ Generated {len(scenarios)} scenarios -> {args.output}")
        
        elif args.command == "export":
            model = cls(use_llm=False)
            if os.path.exists(args.model):
                model.load(args.model)
            model.export_onnx(args.output)
        
        else:
            parser.print_help()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_model(**kwargs) -> SalesforceFlowAIModel:
    """Create a new model instance"""
    return SalesforceFlowAIModel(**kwargs)


def train_model(flows_dir: str = "org_flows", output: str = "flow_model.pkl") -> SalesforceFlowAIModel:
    """Train a model on flows in a directory"""
    model = SalesforceFlowAIModel(use_llm=False)
    
    flows = []
    for flow_file in Path(flows_dir).glob("*.json"):
        if flow_file.name.startswith("_"):
            continue
        with open(flow_file) as f:
            flows.append(json.load(f))
    
    model.train(flows)
    model.save(output)
    
    return model


def load_model(path: str = "flow_model.pkl") -> SalesforceFlowAIModel:
    """Load a pre-trained model"""
    model = SalesforceFlowAIModel(model_path=path)
    return model


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    SalesforceFlowAIModel.cli()

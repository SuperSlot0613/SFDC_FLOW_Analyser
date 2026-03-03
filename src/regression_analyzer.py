"""
Regression Analyzer for comparing Flow metadata against baselines.
Detects changes, evaluates impact, and determines if updates are safe.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib


class ChangeType(Enum):
    """Types of changes detected."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ChangeSeverity(Enum):
    """Severity of a change."""
    CRITICAL = "critical"      # Breaking change, blocks update
    HIGH = "high"              # Significant change, needs review
    MEDIUM = "medium"          # Moderate change, likely safe
    LOW = "low"                # Minor change, safe to update
    INFO = "info"              # Informational, no impact


class UpdateDecision(Enum):
    """Decision on whether to update baseline."""
    APPROVE = "approve"        # Safe to update
    REJECT = "reject"          # Do not update, breaking changes
    REVIEW = "review"          # Needs manual review
    AUTO_APPROVE = "auto_approve"  # Automatically approved (minor changes)


@dataclass
class FlowChange:
    """Represents a change in a flow element."""
    element_type: str          # e.g., 'actionCall', 'decision', 'assignment'
    element_name: str
    change_type: str           # ChangeType value
    severity: str              # ChangeSeverity value
    description: str
    baseline_value: Any
    current_value: Any
    impact_analysis: str
    is_breaking: bool


@dataclass
class FlowComparison:
    """Comparison result for a single flow."""
    flow_name: str
    change_type: str           # ChangeType value (for the whole flow)
    baseline_checksum: str
    current_checksum: str
    changes: List[FlowChange]
    breaking_changes_count: int
    total_changes_count: int
    risk_score: float          # 0-100, higher = more risky
    recommendation: str
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['changes'] = [asdict(c) for c in self.changes]
        return result


@dataclass 
class RegressionReport:
    """Complete regression analysis report."""
    baseline_id: str
    baseline_name: str
    analysis_timestamp: str
    flows_compared: int
    flows_added: int
    flows_removed: int
    flows_modified: int
    flows_unchanged: int
    total_breaking_changes: int
    overall_risk_score: float
    update_decision: str       # UpdateDecision value
    decision_reason: str
    flow_comparisons: List[FlowComparison]
    summary: Dict
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['flow_comparisons'] = [fc.to_dict() for fc in self.flow_comparisons]
        return result


class RegressionAnalyzer:
    """
    Analyzes differences between current Flow metadata and baseline.
    Determines if changes are safe and whether baseline should be updated.
    """
    
    # Element types and their breaking change potential
    ELEMENT_WEIGHTS = {
        'start': 10,           # Starting point changes are critical
        'actionCalls': 8,      # API calls can break integrations
        'decisions': 7,        # Logic changes can break flow
        'recordCreates': 7,    # DML operations are significant
        'recordUpdates': 7,
        'recordDeletes': 8,    # Deletes are high risk
        'recordLookups': 5,    # Query changes moderate risk
        'assignments': 4,      # Variable assignments lower risk
        'screens': 3,          # UI changes usually safer
        'subflows': 6,         # Subflow changes can cascade
        'loops': 5,
        'variables': 3,
        'formulas': 4,
        'constants': 2,
        'textTemplates': 2,
    }
    
    # Thresholds for update decisions
    THRESHOLDS = {
        'auto_approve_max_risk': 20,      # Auto-approve if risk <= 20
        'review_max_risk': 60,            # Review if risk <= 60
        'max_breaking_changes': 0,        # Any breaking change blocks update
        'high_risk_element_threshold': 3,  # Max high-risk element changes
    }
    
    def __init__(self, baseline_manager: 'BaselineManager', flow_analyzer: 'FlowAnalysisEngine'):
        """
        Initialize regression analyzer.
        
        Args:
            baseline_manager: Manager for baseline storage
            flow_analyzer: Engine for analyzing flows
        """
        self.baseline_manager = baseline_manager
        self.flow_analyzer = flow_analyzer
    
    def _calculate_element_checksum(self, element: Any) -> str:
        """Calculate checksum for an element."""
        json_str = json.dumps(element, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _extract_elements(self, flow_metadata: Dict) -> Dict[str, List[Dict]]:
        """Extract all elements from flow metadata."""
        metadata = flow_metadata.get('Metadata', {})
        
        elements = {}
        for element_type in self.ELEMENT_WEIGHTS.keys():
            element_list = metadata.get(element_type, [])
            if element_list is None:
                element_list = []
            elif not isinstance(element_list, list):
                element_list = [element_list]
            elements[element_type] = element_list
        
        return elements
    
    def _compare_elements(
        self,
        baseline_elements: Dict[str, List],
        current_elements: Dict[str, List],
        flow_name: str
    ) -> List[FlowChange]:
        """Compare elements between baseline and current."""
        changes = []
        
        for element_type, weight in self.ELEMENT_WEIGHTS.items():
            baseline_list = baseline_elements.get(element_type, [])
            current_list = current_elements.get(element_type, [])
            
            # Create name-based lookup
            baseline_by_name = {
                e.get('name', f'unnamed_{i}'): e 
                for i, e in enumerate(baseline_list)
            }
            current_by_name = {
                e.get('name', f'unnamed_{i}'): e 
                for i, e in enumerate(current_list)
            }
            
            all_names = set(baseline_by_name.keys()) | set(current_by_name.keys())
            
            for name in all_names:
                baseline_elem = baseline_by_name.get(name)
                current_elem = current_by_name.get(name)
                
                if baseline_elem and not current_elem:
                    # Element removed
                    is_breaking = weight >= 6
                    changes.append(FlowChange(
                        element_type=element_type,
                        element_name=name,
                        change_type=ChangeType.REMOVED.value,
                        severity=ChangeSeverity.HIGH.value if is_breaking else ChangeSeverity.MEDIUM.value,
                        description=f"Element '{name}' of type '{element_type}' was removed",
                        baseline_value=baseline_elem,
                        current_value=None,
                        impact_analysis=self._analyze_removal_impact(element_type, baseline_elem, flow_name),
                        is_breaking=is_breaking
                    ))
                    
                elif current_elem and not baseline_elem:
                    # Element added
                    changes.append(FlowChange(
                        element_type=element_type,
                        element_name=name,
                        change_type=ChangeType.ADDED.value,
                        severity=ChangeSeverity.LOW.value,
                        description=f"New element '{name}' of type '{element_type}' was added",
                        baseline_value=None,
                        current_value=current_elem,
                        impact_analysis=self._analyze_addition_impact(element_type, current_elem, flow_name),
                        is_breaking=False
                    ))
                    
                elif baseline_elem and current_elem:
                    # Check if modified
                    baseline_checksum = self._calculate_element_checksum(baseline_elem)
                    current_checksum = self._calculate_element_checksum(current_elem)
                    
                    if baseline_checksum != current_checksum:
                        # Element modified
                        modification_severity, is_breaking = self._assess_modification(
                            element_type, baseline_elem, current_elem, weight
                        )
                        changes.append(FlowChange(
                            element_type=element_type,
                            element_name=name,
                            change_type=ChangeType.MODIFIED.value,
                            severity=modification_severity,
                            description=f"Element '{name}' of type '{element_type}' was modified",
                            baseline_value=baseline_elem,
                            current_value=current_elem,
                            impact_analysis=self._analyze_modification_impact(
                                element_type, baseline_elem, current_elem, flow_name
                            ),
                            is_breaking=is_breaking
                        ))
        
        return changes
    
    def _analyze_removal_impact(self, element_type: str, element: Dict, flow_name: str) -> str:
        """Analyze impact of removing an element."""
        element_name = element.get('name', 'unnamed')
        
        impacts = []
        
        if element_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            obj_type = element.get('object', element.get('inputReference', 'unknown'))
            impacts.append(f"DML operation on {obj_type} will no longer execute")
            
        elif element_type == 'actionCalls':
            action_name = element.get('actionName', 'unknown')
            impacts.append(f"Action '{action_name}' will no longer be called")
            impacts.append("External integrations may be affected")
            
        elif element_type == 'decisions':
            impacts.append(f"Decision logic '{element_name}' removed")
            impacts.append("Flow routing may be affected")
            
        elif element_type == 'subflows':
            subflow_name = element.get('flowName', 'unknown')
            impacts.append(f"Subflow '{subflow_name}' will no longer be invoked")
            
        if not impacts:
            impacts.append(f"Removal of {element_type} element may affect flow behavior")
        
        return " | ".join(impacts)
    
    def _analyze_addition_impact(self, element_type: str, element: Dict, flow_name: str) -> str:
        """Analyze impact of adding an element."""
        element_name = element.get('name', 'unnamed')
        
        impacts = []
        
        if element_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            obj_type = element.get('object', element.get('inputReference', 'unknown'))
            impacts.append(f"New DML operation on {obj_type}")
            
        elif element_type == 'actionCalls':
            action_name = element.get('actionName', 'unknown')
            impacts.append(f"New action '{action_name}' will be called")
            
        elif element_type == 'decisions':
            impacts.append(f"New decision logic '{element_name}' added")
            
        if not impacts:
            impacts.append(f"New {element_type} element added to flow")
        
        return " | ".join(impacts)
    
    def _analyze_modification_impact(
        self, 
        element_type: str, 
        baseline: Dict, 
        current: Dict, 
        flow_name: str
    ) -> str:
        """Analyze impact of modifying an element."""
        impacts = []
        element_name = baseline.get('name', 'unnamed')
        
        # Check specific field changes
        if element_type == 'decisions':
            # Check if conditions changed
            baseline_rules = baseline.get('rules', [])
            current_rules = current.get('rules', [])
            if len(baseline_rules) != len(current_rules):
                impacts.append(f"Number of decision rules changed: {len(baseline_rules)} → {len(current_rules)}")
            else:
                impacts.append("Decision rule conditions may have changed")
                
        elif element_type == 'actionCalls':
            baseline_action = baseline.get('actionName', '')
            current_action = current.get('actionName', '')
            if baseline_action != current_action:
                impacts.append(f"Action changed: {baseline_action} → {current_action}")
            else:
                impacts.append("Action parameters modified")
                
        elif element_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            baseline_obj = baseline.get('object', baseline.get('inputReference', ''))
            current_obj = current.get('object', current.get('inputReference', ''))
            if baseline_obj != current_obj:
                impacts.append(f"Target object changed: {baseline_obj} → {current_obj}")
            else:
                impacts.append("DML field mappings modified")
        
        elif element_type == 'subflows':
            baseline_flow = baseline.get('flowName', '')
            current_flow = current.get('flowName', '')
            if baseline_flow != current_flow:
                impacts.append(f"Subflow changed: {baseline_flow} → {current_flow}")
        
        if not impacts:
            impacts.append(f"Element '{element_name}' configuration changed")
        
        return " | ".join(impacts)
    
    def _assess_modification(
        self, 
        element_type: str, 
        baseline: Dict, 
        current: Dict, 
        weight: int
    ) -> Tuple[str, bool]:
        """
        Assess the severity of a modification.
        
        Returns:
            Tuple of (severity, is_breaking)
        """
        # Critical changes
        critical_fields = {
            'actionCalls': ['actionName', 'actionType'],
            'decisions': ['defaultConnector', 'rules'],
            'recordCreates': ['object', 'inputReference'],
            'recordUpdates': ['object', 'inputReference', 'filterLogic'],
            'recordDeletes': ['object', 'inputReference', 'filterLogic'],
            'subflows': ['flowName'],
            'start': ['triggerType', 'object', 'schedule'],
        }
        
        element_critical_fields = critical_fields.get(element_type, [])
        
        for field in element_critical_fields:
            baseline_val = baseline.get(field)
            current_val = current.get(field)
            if baseline_val != current_val:
                return ChangeSeverity.CRITICAL.value, True
        
        # High severity for high-weight elements
        if weight >= 7:
            return ChangeSeverity.HIGH.value, False
        elif weight >= 5:
            return ChangeSeverity.MEDIUM.value, False
        else:
            return ChangeSeverity.LOW.value, False
    
    def _calculate_flow_checksum(self, flow_metadata: Dict) -> str:
        """Calculate checksum for flow comparison."""
        elements = self._extract_elements(flow_metadata)
        return hashlib.md5(
            json.dumps(elements, sort_keys=True, default=str).encode()
        ).hexdigest()
    
    def _calculate_risk_score(self, changes: List[FlowChange]) -> float:
        """
        Calculate overall risk score for changes.
        
        Returns:
            Risk score from 0-100
        """
        if not changes:
            return 0.0
        
        total_score = 0.0
        
        severity_scores = {
            ChangeSeverity.CRITICAL.value: 30,
            ChangeSeverity.HIGH.value: 20,
            ChangeSeverity.MEDIUM.value: 10,
            ChangeSeverity.LOW.value: 3,
            ChangeSeverity.INFO.value: 1,
        }
        
        change_type_multipliers = {
            ChangeType.REMOVED.value: 1.5,
            ChangeType.MODIFIED.value: 1.2,
            ChangeType.ADDED.value: 0.8,
        }
        
        for change in changes:
            base_score = severity_scores.get(change.severity, 5)
            multiplier = change_type_multipliers.get(change.change_type, 1.0)
            
            # Additional multiplier for breaking changes
            if change.is_breaking:
                multiplier *= 2.0
            
            # Element weight multiplier
            element_weight = self.ELEMENT_WEIGHTS.get(change.element_type, 5) / 10
            
            total_score += base_score * multiplier * element_weight
        
        # Normalize to 0-100
        return min(100.0, total_score)
    
    def _make_update_decision(
        self, 
        breaking_changes: int,
        risk_score: float,
        changes: List[FlowChange]
    ) -> Tuple[UpdateDecision, str]:
        """
        Make decision on whether to update baseline.
        
        Returns:
            Tuple of (decision, reason)
        """
        # Check for breaking changes
        if breaking_changes > self.THRESHOLDS['max_breaking_changes']:
            return (
                UpdateDecision.REJECT,
                f"Found {breaking_changes} breaking change(s) that could affect existing functionality"
            )
        
        # Check risk score
        if risk_score <= self.THRESHOLDS['auto_approve_max_risk']:
            return (
                UpdateDecision.AUTO_APPROVE,
                f"Low risk score ({risk_score:.1f}) - changes are minor and safe"
            )
        
        if risk_score <= self.THRESHOLDS['review_max_risk']:
            return (
                UpdateDecision.REVIEW,
                f"Moderate risk score ({risk_score:.1f}) - manual review recommended"
            )
        
        # High risk
        high_risk_changes = [c for c in changes if c.severity in 
                           [ChangeSeverity.CRITICAL.value, ChangeSeverity.HIGH.value]]
        
        if len(high_risk_changes) > self.THRESHOLDS['high_risk_element_threshold']:
            return (
                UpdateDecision.REJECT,
                f"High risk ({risk_score:.1f}) with {len(high_risk_changes)} critical/high severity changes"
            )
        
        return (
            UpdateDecision.REVIEW,
            f"High risk score ({risk_score:.1f}) - requires careful review before updating"
        )
    
    def compare_flow(
        self, 
        baseline_flow: Dict, 
        current_flow: Dict
    ) -> FlowComparison:
        """
        Compare a single flow against its baseline.
        
        Args:
            baseline_flow: Flow data from baseline
            current_flow: Current flow metadata
            
        Returns:
            FlowComparison with detailed changes
        """
        flow_name = baseline_flow.get('flow_name', 'unknown')
        
        baseline_metadata = baseline_flow.get('metadata', {})
        
        # Calculate checksums
        baseline_checksum = baseline_flow.get('checksum', self._calculate_flow_checksum(baseline_metadata))
        current_checksum = self._calculate_flow_checksum(current_flow)
        
        # If checksums match, no changes
        if baseline_checksum == current_checksum:
            return FlowComparison(
                flow_name=flow_name,
                change_type=ChangeType.UNCHANGED.value,
                baseline_checksum=baseline_checksum,
                current_checksum=current_checksum,
                changes=[],
                breaking_changes_count=0,
                total_changes_count=0,
                risk_score=0.0,
                recommendation="No changes detected - flow matches baseline"
            )
        
        # Extract and compare elements
        baseline_elements = self._extract_elements(baseline_metadata)
        current_elements = self._extract_elements(current_flow)
        
        changes = self._compare_elements(baseline_elements, current_elements, flow_name)
        
        # Calculate metrics
        breaking_count = sum(1 for c in changes if c.is_breaking)
        risk_score = self._calculate_risk_score(changes)
        
        # Generate recommendation
        if breaking_count > 0:
            recommendation = f"⚠️ {breaking_count} breaking change(s) detected - review carefully before updating"
        elif risk_score > 50:
            recommendation = "High risk changes - manual review recommended"
        elif risk_score > 20:
            recommendation = "Moderate changes - verify functionality before updating"
        else:
            recommendation = "Minor changes - safe to update baseline"
        
        return FlowComparison(
            flow_name=flow_name,
            change_type=ChangeType.MODIFIED.value,
            baseline_checksum=baseline_checksum,
            current_checksum=current_checksum,
            changes=changes,
            breaking_changes_count=breaking_count,
            total_changes_count=len(changes),
            risk_score=risk_score,
            recommendation=recommendation
        )
    
    def run_regression(
        self, 
        current_flows: List[Dict],
        baseline_id: Optional[str] = None
    ) -> RegressionReport:
        """
        Run full regression analysis comparing current flows to baseline.
        
        Args:
            current_flows: List of current flow metadata from Salesforce
            baseline_id: Specific baseline to compare against (uses active if not specified)
            
        Returns:
            Complete RegressionReport
        """
        timestamp = datetime.now().isoformat()
        
        # Get baseline
        if baseline_id:
            baseline = self.baseline_manager.get_baseline(baseline_id)
        else:
            baseline = self.baseline_manager.get_active_baseline()
        
        if not baseline:
            raise ValueError("No baseline available for comparison")
        
        baseline_metadata = baseline.get('metadata', {})
        baseline_flows = baseline.get('flows', [])
        
        # Create lookup maps
        baseline_by_name = {f['flow_name']: f for f in baseline_flows}
        current_by_name = {}
        for flow in current_flows:
            name = (
                flow.get('FullName') or 
                flow.get('fullName') or 
                flow.get('Metadata', {}).get('fullName') or
                flow.get('_source_file', 'unknown')
            )
            current_by_name[name] = flow
        
        # Track statistics
        flows_added = []
        flows_removed = []
        flows_modified = []
        flows_unchanged = []
        flow_comparisons = []
        
        all_flow_names = set(baseline_by_name.keys()) | set(current_by_name.keys())
        
        for flow_name in all_flow_names:
            baseline_flow = baseline_by_name.get(flow_name)
            current_flow = current_by_name.get(flow_name)
            
            if baseline_flow and not current_flow:
                # Flow removed
                flows_removed.append(flow_name)
                flow_comparisons.append(FlowComparison(
                    flow_name=flow_name,
                    change_type=ChangeType.REMOVED.value,
                    baseline_checksum=baseline_flow.get('checksum', ''),
                    current_checksum='',
                    changes=[FlowChange(
                        element_type='flow',
                        element_name=flow_name,
                        change_type=ChangeType.REMOVED.value,
                        severity=ChangeSeverity.CRITICAL.value,
                        description=f"Flow '{flow_name}' was removed from the org",
                        baseline_value=baseline_flow,
                        current_value=None,
                        impact_analysis="Entire flow has been removed - all functionality lost",
                        is_breaking=True
                    )],
                    breaking_changes_count=1,
                    total_changes_count=1,
                    risk_score=100.0,
                    recommendation="⚠️ CRITICAL: Flow removed - verify this is intentional"
                ))
                
            elif current_flow and not baseline_flow:
                # Flow added
                flows_added.append(flow_name)
                flow_comparisons.append(FlowComparison(
                    flow_name=flow_name,
                    change_type=ChangeType.ADDED.value,
                    baseline_checksum='',
                    current_checksum=self._calculate_flow_checksum(current_flow),
                    changes=[FlowChange(
                        element_type='flow',
                        element_name=flow_name,
                        change_type=ChangeType.ADDED.value,
                        severity=ChangeSeverity.LOW.value,
                        description=f"New flow '{flow_name}' added to the org",
                        baseline_value=None,
                        current_value=current_flow,
                        impact_analysis="New flow added - no impact on existing functionality",
                        is_breaking=False
                    )],
                    breaking_changes_count=0,
                    total_changes_count=1,
                    risk_score=5.0,
                    recommendation="New flow - safe to add to baseline"
                ))
                
            else:
                # Compare existing flow
                comparison = self.compare_flow(baseline_flow, current_flow)
                flow_comparisons.append(comparison)
                
                if comparison.change_type == ChangeType.UNCHANGED.value:
                    flows_unchanged.append(flow_name)
                else:
                    flows_modified.append(flow_name)
        
        # Calculate totals
        total_breaking = sum(fc.breaking_changes_count for fc in flow_comparisons)
        overall_risk = sum(fc.risk_score for fc in flow_comparisons) / max(len(flow_comparisons), 1)
        
        # Make update decision
        all_changes = []
        for fc in flow_comparisons:
            all_changes.extend(fc.changes)
        
        decision, reason = self._make_update_decision(total_breaking, overall_risk, all_changes)
        
        # Build summary
        summary = {
            'baseline_version': baseline_metadata.get('version'),
            'baseline_created': baseline_metadata.get('created_at'),
            'comparison_timestamp': timestamp,
            'statistics': {
                'total_flows_compared': len(all_flow_names),
                'added': len(flows_added),
                'removed': len(flows_removed),
                'modified': len(flows_modified),
                'unchanged': len(flows_unchanged),
            },
            'risk_assessment': {
                'overall_risk_score': round(overall_risk, 2),
                'total_breaking_changes': total_breaking,
                'total_changes': len(all_changes),
            },
            'flows_added': flows_added,
            'flows_removed': flows_removed,
            'flows_modified': flows_modified,
        }
        
        return RegressionReport(
            baseline_id=baseline_metadata.get('id', ''),
            baseline_name=baseline_metadata.get('name', ''),
            analysis_timestamp=timestamp,
            flows_compared=len(all_flow_names),
            flows_added=len(flows_added),
            flows_removed=len(flows_removed),
            flows_modified=len(flows_modified),
            flows_unchanged=len(flows_unchanged),
            total_breaking_changes=total_breaking,
            overall_risk_score=overall_risk,
            update_decision=decision.value,
            decision_reason=reason,
            flow_comparisons=flow_comparisons,
            summary=summary
        )
    
    def should_update_baseline(self, report: RegressionReport) -> bool:
        """
        Determine if baseline should be updated based on report.
        
        Args:
            report: Regression report from analysis
            
        Returns:
            True if safe to update, False otherwise
        """
        return report.update_decision in [
            UpdateDecision.APPROVE.value,
            UpdateDecision.AUTO_APPROVE.value
        ]
    
    def validate_update_safety(
        self,
        current_flows: List[Dict],
        current_analysis: List[Dict],
        baseline_id: Optional[str] = None
    ) -> Dict:
        """
        Validate if updating baseline is safe.
        Performs additional checks beyond regression comparison.
        
        Args:
            current_flows: Current flow metadata
            current_analysis: Current analysis results
            baseline_id: Baseline to validate against
            
        Returns:
            Validation result with safety assessment
        """
        validation_result = {
            'is_safe': True,
            'warnings': [],
            'errors': [],
            'checks_performed': []
        }
        
        # Get baseline for comparison
        if baseline_id:
            baseline = self.baseline_manager.get_baseline(baseline_id)
        else:
            baseline = self.baseline_manager.get_active_baseline()
        
        if not baseline:
            validation_result['is_safe'] = True
            validation_result['checks_performed'].append("No existing baseline - initial baseline creation")
            return validation_result
        
        baseline_flows = baseline.get('flows', [])
        
        # Check 1: No reduction in flow count (unless intentional)
        baseline_count = len(baseline_flows)
        current_count = len(current_flows)
        
        if current_count < baseline_count:
            missing_count = baseline_count - current_count
            validation_result['warnings'].append(
                f"Flow count reduced by {missing_count} ({baseline_count} → {current_count})"
            )
        validation_result['checks_performed'].append(f"Flow count check: {baseline_count} → {current_count}")
        
        # Check 2: Critical issues haven't increased significantly
        baseline_critical = 0
        for flow in baseline_flows:
            issues = flow.get('analysis_summary', {}).get('issues', [])
            baseline_critical += sum(1 for i in issues if i.get('severity') == 'critical')
        
        current_critical = 0
        for analysis in current_analysis:
            issues = analysis.get('issues', [])
            current_critical += sum(1 for i in issues if i.get('severity') == 'critical')
        
        if current_critical > baseline_critical:
            new_critical = current_critical - baseline_critical
            validation_result['warnings'].append(
                f"Critical issues increased by {new_critical} ({baseline_critical} → {current_critical})"
            )
        validation_result['checks_performed'].append(f"Critical issues check: {baseline_critical} → {current_critical}")
        
        # Check 3: No removed flows that had dependencies
        baseline_names = {f['flow_name'] for f in baseline_flows}
        current_names = set()
        for flow in current_flows:
            name = (
                flow.get('FullName') or 
                flow.get('fullName') or 
                flow.get('Metadata', {}).get('fullName') or
                flow.get('_source_file', 'unknown')
            )
            current_names.add(name)
        
        removed_flows = baseline_names - current_names
        if removed_flows:
            # Check if removed flows were referenced by others
            for flow in baseline_flows:
                metadata = flow.get('metadata', {}).get('Metadata', {})
                subflows = metadata.get('subflows', []) or []
                for subflow in subflows:
                    subflow_name = subflow.get('flowName', '')
                    if subflow_name in removed_flows:
                        validation_result['errors'].append(
                            f"Removed flow '{subflow_name}' is still referenced by '{flow['flow_name']}'"
                        )
                        validation_result['is_safe'] = False
        
        validation_result['checks_performed'].append(f"Removed flows dependency check: {len(removed_flows)} removed")
        
        # Check 4: Process type hasn't changed (could indicate misconfiguration)
        for flow in baseline_flows:
            flow_name = flow['flow_name']
            baseline_type = flow.get('metadata', {}).get('Metadata', {}).get('processType')
            
            for current in current_flows:
                current_name = (
                    current.get('FullName') or 
                    current.get('fullName') or 
                    current.get('Metadata', {}).get('fullName')
                )
                if current_name == flow_name:
                    current_type = current.get('Metadata', {}).get('processType')
                    if baseline_type and current_type and baseline_type != current_type:
                        validation_result['errors'].append(
                            f"Flow '{flow_name}' process type changed: {baseline_type} → {current_type}"
                        )
                        validation_result['is_safe'] = False
                    break
        
        validation_result['checks_performed'].append("Process type consistency check")
        
        # Final determination
        if validation_result['errors']:
            validation_result['is_safe'] = False
        
        return validation_result


if __name__ == "__main__":
    print("=" * 60)
    print("Regression Analyzer Module")
    print("=" * 60)
    print("\nThis module provides:")
    print("  - Flow comparison against baselines")
    print("  - Change detection and categorization")
    print("  - Breaking change identification")
    print("  - Risk scoring")
    print("  - Update decision making")
    print("\nUse RegressionModel for full functionality.")

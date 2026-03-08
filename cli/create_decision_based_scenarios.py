#!/usr/bin/env python3
"""
Create Decision-Based Test Scenarios
====================================

This script analyzes your REAL org flows and generates intelligent test scenarios
based on the actual decision conditions, triggers, and logic in each flow.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory and src to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.model import create_model_from_config


def analyze_flow_decisions(flow_data):
    """
    Extract decision conditions, triggers, and logic from a flow
    """
    metadata = flow_data.get('Metadata', {})
    
    analysis = {
        'flow_name': flow_data.get('MasterLabel', 'Unknown'),
        'developer_name': flow_data.get('FullName', ''),
        'process_type': flow_data.get('ProcessType', ''),
        'trigger_type': None,
        'trigger_object': None,
        'trigger_conditions': [],
        'decisions': [],
        'record_lookups': [],
        'record_creates': [],
        'record_updates': [],
        'apex_calls': [],
        'email_alerts': [],
        'chatter_posts': [],
        'screens': [],
        'formulas': [],
        'variables': [],
        'loops': []
    }
    
    # Extract trigger information from start element
    start = metadata.get('start', {})
    if start:
        analysis['trigger_type'] = start.get('triggerType')
        analysis['trigger_object'] = start.get('object')
        analysis['record_trigger_type'] = start.get('recordTriggerType')
        analysis['requires_change'] = start.get('doesRequireRecordChangedToMeetCriteria')
        
        # Extract trigger filters/conditions
        filters = start.get('filters', [])
        for f in filters:
            analysis['trigger_conditions'].append({
                'field': f.get('field'),
                'operator': f.get('operator'),
                'value': extract_value(f.get('value', {}))
            })
    
    # Extract decisions with their conditions
    decisions = metadata.get('decisions', [])
    for decision in decisions:
        decision_info = {
            'name': decision.get('name'),
            'label': decision.get('label'),
            'rules': []
        }
        
        for rule in decision.get('rules', []):
            rule_info = {
                'name': rule.get('name'),
                'label': rule.get('label'),
                'condition_logic': rule.get('conditionLogic', 'and'),
                'conditions': []
            }
            
            for condition in rule.get('conditions', []):
                rule_info['conditions'].append({
                    'left': condition.get('leftValueReference'),
                    'operator': condition.get('operator'),
                    'right': extract_value(condition.get('rightValue', {}))
                })
            
            decision_info['rules'].append(rule_info)
        
        analysis['decisions'].append(decision_info)
    
    # Extract record lookups with their filters
    lookups = metadata.get('recordLookups', [])
    for lookup in lookups:
        lookup_info = {
            'name': lookup.get('name'),
            'label': lookup.get('label'),
            'object': lookup.get('object'),
            'filters': []
        }
        
        for f in lookup.get('filters', []):
            lookup_info['filters'].append({
                'field': f.get('field'),
                'operator': f.get('operator'),
                'value': extract_value(f.get('value', {}))
            })
        
        analysis['record_lookups'].append(lookup_info)
    
    # Extract record creates
    creates = metadata.get('recordCreates', [])
    for create in creates:
        create_info = {
            'name': create.get('name'),
            'label': create.get('label'),
            'object': create.get('object'),
            'fields': []
        }
        
        for assignment in create.get('inputAssignments', []):
            create_info['fields'].append({
                'field': assignment.get('field'),
                'value': extract_value(assignment.get('value', {}))
            })
        
        analysis['record_creates'].append(create_info)
    
    # Extract record updates
    updates = metadata.get('recordUpdates', [])
    for update in updates:
        update_info = {
            'name': update.get('name'),
            'label': update.get('label'),
            'object': update.get('object'),
            'fields': []
        }
        
        for assignment in update.get('inputAssignments', []):
            update_info['fields'].append({
                'field': assignment.get('field'),
                'value': extract_value(assignment.get('value', {}))
            })
        
        analysis['record_updates'].append(update_info)
    
    # Extract action calls
    actions = metadata.get('actionCalls', [])
    for action in actions:
        action_type = action.get('actionType', '')
        action_info = {
            'name': action.get('name'),
            'label': action.get('label'),
            'action_name': action.get('actionName'),
            'action_type': action_type
        }
        
        if action_type == 'apex':
            analysis['apex_calls'].append(action_info)
        elif action_type == 'emailAlert':
            analysis['email_alerts'].append(action_info)
        elif action_type == 'chatterPost':
            analysis['chatter_posts'].append(action_info)
    
    # Extract screens
    screens = metadata.get('screens', [])
    for screen in screens:
        screen_info = {
            'name': screen.get('name'),
            'label': screen.get('label'),
            'fields': []
        }
        
        for field in screen.get('fields', []):
            screen_info['fields'].append({
                'name': field.get('name'),
                'label': field.get('fieldText'),
                'type': field.get('fieldType'),
                'required': field.get('isRequired'),
                'data_type': field.get('dataType')
            })
        
        analysis['screens'].append(screen_info)
    
    # Extract formulas
    formulas = metadata.get('formulas', [])
    for formula in formulas:
        analysis['formulas'].append({
            'name': formula.get('name'),
            'expression': formula.get('expression'),
            'data_type': formula.get('dataType'),
            'description': formula.get('description')
        })
    
    # Extract variables
    variables = metadata.get('variables', [])
    for var in variables:
        analysis['variables'].append({
            'name': var.get('name'),
            'data_type': var.get('dataType'),
            'object_type': var.get('objectType'),
            'is_input': var.get('isInput'),
            'is_output': var.get('isOutput')
        })
    
    # Extract loops
    loops = metadata.get('loops', [])
    for loop in loops:
        analysis['loops'].append({
            'name': loop.get('name'),
            'label': loop.get('label'),
            'collection': loop.get('collectionReference')
        })
    
    return analysis


def extract_value(value_obj):
    """Extract the actual value from a Salesforce value object"""
    if not value_obj:
        return None
    
    # Check each possible value type
    if value_obj.get('stringValue') is not None:
        return value_obj['stringValue']
    elif value_obj.get('numberValue') is not None:
        return value_obj['numberValue']
    elif value_obj.get('booleanValue') is not None:
        return value_obj['booleanValue']
    elif value_obj.get('elementReference'):
        return f"${{{value_obj['elementReference']}}}"
    elif value_obj.get('dateValue'):
        return value_obj['dateValue']
    elif value_obj.get('dateTimeValue'):
        return value_obj['dateTimeValue']
    
    return None


def generate_decision_scenarios(flow_analysis):
    """
    Generate intelligent test scenarios based on flow analysis
    """
    scenarios = []
    flow_name = flow_analysis['flow_name']
    
    # === TRIGGER-BASED SCENARIOS ===
    if flow_analysis['trigger_conditions']:
        for i, trigger in enumerate(flow_analysis['trigger_conditions']):
            # Scenario: What triggers the flow
            scenarios.append({
                'id': f"trigger_{i+1}",
                'category': 'Flow Trigger Conditions',
                'flow': flow_analysis['developer_name'],
                'query': f"When does the '{flow_name}' flow get triggered? Specifically, what condition on {trigger['field']} must be met?",
                'context': f"Trigger: {trigger['field']} {trigger['operator']} {trigger['value']}",
                'expected_analysis': [
                    f"Field: {trigger['field']}",
                    f"Operator: {trigger['operator']}",
                    f"Value: {trigger['value']}"
                ]
            })
            
            # Scenario: Edge case - what if condition not met
            scenarios.append({
                'id': f"trigger_edge_{i+1}",
                'category': 'Flow Trigger Edge Cases',
                'flow': flow_analysis['developer_name'],
                'query': f"What happens in '{flow_name}' if {trigger['field']} is NOT equal to '{trigger['value']}'? Will the flow execute?",
                'context': f"Testing trigger condition: {trigger['field']} {trigger['operator']} {trigger['value']}",
                'expected_analysis': [
                    "Flow will NOT execute",
                    f"Requires {trigger['field']} = {trigger['value']}"
                ]
            })
    
    # === DECISION-BASED SCENARIOS ===
    for decision in flow_analysis['decisions']:
        decision_label = decision.get('label', decision.get('name', 'Unknown'))
        
        for rule in decision.get('rules', []):
            rule_label = rule.get('label', rule.get('name', 'Unknown'))
            conditions = rule.get('conditions', [])
            
            if conditions:
                # Build condition description
                condition_desc = []
                for cond in conditions:
                    condition_desc.append(f"{cond['left']} {cond['operator']} {cond['right']}")
                
                condition_str = f" {rule.get('condition_logic', 'AND')} ".join(condition_desc)
                
                # Scenario: Decision outcome
                scenarios.append({
                    'id': f"decision_{decision['name']}_{rule['name']}",
                    'category': 'Decision Logic Analysis',
                    'flow': flow_analysis['developer_name'],
                    'query': f"In '{flow_name}', explain the decision '{decision_label}' - specifically when does the '{rule_label}' path execute?",
                    'context': f"Conditions: {condition_str}",
                    'expected_analysis': condition_desc
                })
                
                # Scenario: Decision condition details
                for j, cond in enumerate(conditions):
                    if cond['operator'] in ['GreaterThanOrEqualTo', 'GreaterThan', 'LessThan', 'LessThanOrEqualTo']:
                        scenarios.append({
                            'id': f"decision_threshold_{decision['name']}_{j}",
                            'category': 'Decision Thresholds',
                            'flow': flow_analysis['developer_name'],
                            'query': f"What is the threshold value for {cond['left']} in the '{flow_name}' flow? What happens when the value is exactly at, above, or below this threshold?",
                            'context': f"Threshold condition: {cond['left']} {cond['operator']} {cond['right']}",
                            'expected_analysis': [
                                f"Threshold: {cond['right']}",
                                f"Operator: {cond['operator']}"
                            ]
                        })
                    
                    if cond['operator'] == 'IsNull':
                        scenarios.append({
                            'id': f"decision_null_{decision['name']}_{j}",
                            'category': 'Null Value Handling',
                            'flow': flow_analysis['developer_name'],
                            'query': f"How does '{flow_name}' handle null values for {cond['left']}? What path does the flow take when this is null vs not null?",
                            'context': f"Null check: {cond['left']} IsNull = {cond['right']}",
                            'expected_analysis': [
                                f"Checks if {cond['left']} is null",
                                f"Expected null state: {cond['right']}"
                            ]
                        })
                
                # Scenario: What if decision conditions are NOT met
                scenarios.append({
                    'id': f"decision_default_{decision['name']}",
                    'category': 'Default Path Analysis',
                    'flow': flow_analysis['developer_name'],
                    'query': f"In '{flow_name}', what is the default outcome if NONE of the conditions in '{decision_label}' are met? What path does the flow take?",
                    'context': f"Analyzing default connector for decision: {decision_label}",
                    'expected_analysis': [
                        "Default path behavior",
                        "Fallback logic"
                    ]
                })
    
    # === RECORD LOOKUP SCENARIOS ===
    for lookup in flow_analysis['record_lookups']:
        if lookup['filters']:
            filter_desc = [f"{f['field']} {f['operator']} {f['value']}" for f in lookup['filters']]
            
            scenarios.append({
                'id': f"lookup_{lookup['name']}",
                'category': 'Record Lookup Analysis',
                'flow': flow_analysis['developer_name'],
                'query': f"In '{flow_name}', how does the '{lookup['label']}' query work? What records does it fetch from {lookup['object']} and what filters are applied?",
                'context': f"Object: {lookup['object']}, Filters: {', '.join(filter_desc)}",
                'expected_analysis': filter_desc
            })
            
            # What if no records found
            scenarios.append({
                'id': f"lookup_empty_{lookup['name']}",
                'category': 'Empty Result Handling',
                'flow': flow_analysis['developer_name'],
                'query': f"What happens in '{flow_name}' if the '{lookup['label']}' query returns NO records? How does the flow handle this scenario?",
                'context': f"Analyzing null/empty handling for {lookup['object']} query",
                'expected_analysis': [
                    "Null assignment handling",
                    "Downstream decision impact"
                ]
            })
    
    # === RECORD CREATE/UPDATE SCENARIOS ===
    for create in flow_analysis['record_creates']:
        if create['fields']:
            field_list = [f['field'] for f in create['fields']]
            
            scenarios.append({
                'id': f"create_{create['name']}",
                'category': 'Record Creation Analysis',
                'flow': flow_analysis['developer_name'],
                'query': f"In '{flow_name}', what {create['object']} record is created by '{create['label']}'? What fields are set and from where do they get their values?",
                'context': f"Object: {create['object']}, Fields: {', '.join(field_list)}",
                'expected_analysis': [f"{f['field']} = {f['value']}" for f in create['fields']]
            })
    
    for update in flow_analysis['record_updates']:
        if update['fields']:
            scenarios.append({
                'id': f"update_{update['name']}",
                'category': 'Record Update Analysis',
                'flow': flow_analysis['developer_name'],
                'query': f"In '{flow_name}', what changes does '{update['label']}' make to the record? Which fields are modified?",
                'context': f"Object: {update.get('object', 'Unknown')}, Updates: {len(update['fields'])} fields",
                'expected_analysis': [f"{f['field']} -> {f['value']}" for f in update['fields']]
            })
    
    # === APEX CALL SCENARIOS ===
    for apex in flow_analysis['apex_calls']:
        scenarios.append({
            'id': f"apex_{apex['name']}",
            'category': 'Apex Integration Analysis',
            'flow': flow_analysis['developer_name'],
            'query': f"In '{flow_name}', what does the Apex action '{apex['action_name']}' do? What inputs does it receive and what outputs does it return?",
            'context': f"Apex class: {apex['action_name']}",
            'expected_analysis': [
                f"Action: {apex['action_name']}",
                "Input/output mapping"
            ]
        })
        
        # Fault handling
        scenarios.append({
            'id': f"apex_fault_{apex['name']}",
            'category': 'Apex Fault Handling',
            'flow': flow_analysis['developer_name'],
            'query': f"What happens in '{flow_name}' if the Apex callout '{apex['action_name']}' fails? Is there error handling?",
            'context': f"Analyzing fault connector for {apex['action_name']}",
            'expected_analysis': [
                "Fault handling path",
                "Error recovery"
            ]
        })
    
    # === SCREEN FLOW SCENARIOS ===
    for screen in flow_analysis['screens']:
        required_fields = [f for f in screen['fields'] if f.get('required')]
        
        if required_fields:
            scenarios.append({
                'id': f"screen_{screen['name']}_validation",
                'category': 'Screen Validation Analysis',
                'flow': flow_analysis['developer_name'],
                'query': f"In '{flow_name}', what are the required fields on the '{screen['label']}' screen? What validation happens?",
                'context': f"Screen: {screen['label']}, Required fields: {len(required_fields)}",
                'expected_analysis': [f"{f['name']} (required)" for f in required_fields]
            })
        
        if screen['fields']:
            scenarios.append({
                'id': f"screen_{screen['name']}_inputs",
                'category': 'Screen Input Analysis',
                'flow': flow_analysis['developer_name'],
                'query': f"What user inputs are collected on the '{screen['label']}' screen in '{flow_name}'? What types of data are expected?",
                'context': f"Screen fields: {[f['name'] for f in screen['fields']]}",
                'expected_analysis': [f"{f['name']}: {f.get('data_type', f.get('type', 'Unknown'))}" for f in screen['fields']]
            })
    
    # === FORMULA SCENARIOS ===
    for formula in flow_analysis['formulas']:
        scenarios.append({
            'id': f"formula_{formula['name']}",
            'category': 'Formula Analysis',
            'flow': flow_analysis['developer_name'],
            'query': f"In '{flow_name}', explain the formula '{formula['name']}'. What does it calculate and where is the result used?",
            'context': f"Expression: {formula['expression']}",
            'expected_analysis': [
                f"Formula: {formula['expression']}",
                f"Type: {formula['data_type']}"
            ]
        })
    
    # === VARIABLE SCENARIOS ===
    input_vars = [v for v in flow_analysis['variables'] if v.get('is_input')]
    output_vars = [v for v in flow_analysis['variables'] if v.get('is_output')]
    
    if input_vars:
        scenarios.append({
            'id': f"variables_input",
            'category': 'Input Variable Analysis',
            'flow': flow_analysis['developer_name'],
            'query': f"What input variables does '{flow_name}' accept? What data must be passed to this flow for it to execute correctly?",
            'context': f"Input variables: {[v['name'] for v in input_vars]}",
            'expected_analysis': [f"{v['name']}: {v.get('object_type', v.get('data_type', 'Unknown'))}" for v in input_vars]
        })
    
    if output_vars:
        scenarios.append({
            'id': f"variables_output",
            'category': 'Output Variable Analysis',
            'flow': flow_analysis['developer_name'],
            'query': f"What output does '{flow_name}' return? What data can be accessed after this flow completes?",
            'context': f"Output variables: {[v['name'] for v in output_vars]}",
            'expected_analysis': [f"{v['name']}: {v.get('object_type', v.get('data_type', 'Unknown'))}" for v in output_vars]
        })
    
    return scenarios


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         CREATE DECISION-BASED TEST SCENARIOS FROM REAL FLOWS                ║
║                                                                              ║
║   Analyzing your actual flow decisions, conditions, and logic               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Load all flows
    flows_file = os.path.join(PROJECT_ROOT, 'org_flows', '_all_flows.json')
    
    if not os.path.exists(flows_file):
        print("❌ No flows found. Run fetch_org_flows_cli.py first.")
        return
    
    with open(flows_file, 'r') as f:
        flows_data = json.load(f)
    
    flows = flows_data.get('flows', [])
    print(f"📊 Analyzing {len(flows)} flows from your org...\n")
    
    all_scenarios = []
    flow_analyses = []
    
    for flow in flows:
        flow_name = flow.get('MasterLabel', 'Unknown')
        print(f"🔍 Analyzing: {flow_name}")
        
        # Analyze flow structure
        analysis = analyze_flow_decisions(flow)
        flow_analyses.append(analysis)
        
        # Print analysis summary
        print(f"   • Trigger: {analysis['trigger_type'] or 'None'} on {analysis['trigger_object'] or 'N/A'}")
        print(f"   • Trigger Conditions: {len(analysis['trigger_conditions'])}")
        print(f"   • Decisions: {len(analysis['decisions'])}")
        print(f"   • Record Lookups: {len(analysis['record_lookups'])}")
        print(f"   • Record Creates: {len(analysis['record_creates'])}")
        print(f"   • Record Updates: {len(analysis['record_updates'])}")
        print(f"   • Apex Calls: {len(analysis['apex_calls'])}")
        print(f"   • Screens: {len(analysis['screens'])}")
        print(f"   • Formulas: {len(analysis['formulas'])}")
        
        # Generate scenarios for this flow
        scenarios = generate_decision_scenarios(analysis)
        all_scenarios.extend(scenarios)
        print(f"   ✅ Generated {len(scenarios)} scenarios")
        print()
    
    # Group scenarios by category
    categories = {}
    for scenario in all_scenarios:
        cat = scenario['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(scenario)
    
    # Display summary
    print("\n" + "=" * 80)
    print("  SCENARIO SUMMARY")
    print("=" * 80)
    print(f"\n📊 Total Scenarios Generated: {len(all_scenarios)}\n")
    print("📋 Scenarios by Category:")
    for cat, scenarios in sorted(categories.items()):
        print(f"   • {cat}: {len(scenarios)}")
    
    # Save scenarios
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    os.makedirs(data_dir, exist_ok=True)  # Create data directory if it doesn't exist
    
    scenarios_file = os.path.join(data_dir, 'decision_based_scenarios.json')
    with open(scenarios_file, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_scenarios': len(all_scenarios),
            'flows_analyzed': len(flows),
            'categories': list(categories.keys()),
            'scenarios': all_scenarios
        }, f, indent=2)
    
    print(f"\n✅ Saved {len(all_scenarios)} scenarios to: data/decision_based_scenarios.json")
    
    # Save flow analyses
    analyses_file = os.path.join(data_dir, 'flow_analyses.json')
    with open(analyses_file, 'w') as f:
        json.dump({
            'analyzed_at': datetime.now().isoformat(),
            'flows': flow_analyses
        }, f, indent=2)
    
    print(f"✅ Saved flow analyses to: data/flow_analyses.json")
    
    # Display sample scenarios
    print("\n" + "=" * 80)
    print("  SAMPLE DECISION-BASED SCENARIOS")
    print("=" * 80)
    
    # Show first 3 scenarios from different categories
    shown_categories = set()
    sample_count = 0
    
    for scenario in all_scenarios:
        cat = scenario['category']
        if cat not in shown_categories and sample_count < 10:
            shown_categories.add(cat)
            sample_count += 1
            print(f"\n📌 [{cat}] Flow: {scenario['flow']}")
            print(f"   Query: {scenario['query']}")
            print(f"   Context: {scenario['context']}")
    
    print("\n" + "=" * 80)
    print("  NEXT STEPS")
    print("=" * 80)
    print(f"""
🚀 To run these decision-based scenarios:

   python3 run_decision_scenarios.py --max 10
   python3 run_decision_scenarios.py --category "Decision Logic Analysis"
   python3 run_decision_scenarios.py --flow "Opportunity_Won_Account_Priority_Actions"
   python3 run_decision_scenarios.py --all

📁 Files Created:
   • decision_based_scenarios.json - {len(all_scenarios)} intelligent scenarios
   • flow_analyses.json - Detailed flow structure analysis
""")


if __name__ == "__main__":
    main()

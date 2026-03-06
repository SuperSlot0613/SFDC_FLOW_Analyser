#!/usr/bin/env python3
"""
Run Decision-Based Test Scenarios
=================================

This script runs intelligent test scenarios generated from your actual flow
decisions, conditions, and logic.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory and src to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.model import create_model_from_config


def load_scenarios():
    """Load decision-based scenarios"""
    scenarios_file = os.path.join(PROJECT_ROOT, 'data', 'decision_based_scenarios.json')
    
    if not os.path.exists(scenarios_file):
        print("❌ No scenarios found. Run create_decision_based_scenarios.py first.")
        return None
    
    with open(scenarios_file, 'r') as f:
        return json.load(f)


def load_flow(flow_name):
    """Load flow metadata by developer name"""
    # Try exact filename first
    flow_file = os.path.join(PROJECT_ROOT, 'org_flows', f'{flow_name}.json')
    
    if os.path.exists(flow_file):
        with open(flow_file, 'r') as f:
            return json.load(f)
    
    # Try loading from _all_flows.json (always works)
    all_flows_file = os.path.join(PROJECT_ROOT, 'org_flows', '_all_flows.json')
    if os.path.exists(all_flows_file):
        with open(all_flows_file, 'r') as f:
            all_flows = json.load(f)
            for flow in all_flows.get('flows', []):
                if flow.get('FullName') == flow_name:
                    return flow
                # Also try matching without case sensitivity
                if flow.get('FullName', '').lower() == flow_name.lower():
                    return flow
    
    return None


# Pre-load all flows at module level
_all_flows_cache = None

def get_all_flows():
    """Get all flows (cached)"""
    global _all_flows_cache
    if _all_flows_cache is None:
        all_flows_file = os.path.join(PROJECT_ROOT, 'org_flows', '_all_flows.json')
        if os.path.exists(all_flows_file):
            with open(all_flows_file, 'r') as f:
                _all_flows_cache = json.load(f).get('flows', [])
        else:
            _all_flows_cache = []
    return _all_flows_cache


def load_flow_from_cache(flow_name):
    """Load flow from cache by developer name"""
    flows = get_all_flows()
    for flow in flows:
        if flow.get('FullName') == flow_name:
            return flow
    return None


def run_scenario(model, scenario, flow_metadata):
    """Run a single scenario against the model and validate against baseline"""
    query = scenario['query']
    
    # Add context to the query
    enhanced_query = f"""
{query}

Additional Context:
- Flow Developer Name: {scenario['flow']}
- Analysis Focus: {scenario['category']}

IMPORTANT: Answer based ONLY on the actual flow metadata provided.
Quote exact values from the metadata. Do NOT guess or fabricate values.
"""
    
    try:
        start_time = datetime.now()
        response = model.query(enhanced_query, context_metadata=flow_metadata)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Validate AI response against expected keywords from scenario
        validation = validate_response(response, scenario, flow_metadata)
        
        return {
            'success': True,
            'response': response,
            'elapsed_seconds': elapsed,
            'validation': validation
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'elapsed_seconds': 0,
            'validation': {'status': 'ERROR', 'issues': [str(e)]}
        }


def validate_response(response, scenario, flow_metadata):
    """
    Validate the AI response against the actual baseline flow metadata.
    
    This checks:
    1. Expected keywords from scenario are present in the response
    2. Values mentioned in the response match the actual flow metadata
    3. The AI didn't fabricate incorrect values
    """
    issues = []
    warnings = []
    response_lower = response.lower()
    
    # 1. Check expected keywords (scenarios use 'expected_analysis' field)
    expected = scenario.get('expected_keywords', scenario.get('expected_analysis', []))
    matched_keywords = []
    missing_keywords = []
    
    for keyword in expected:
        keyword_lower = keyword.lower().strip()
        # Flexible matching: check if the core content is in the response
        # Handle prefixed keywords like "Field: Product__c" or "Value: Credit Card"
        core_value = keyword_lower
        if ':' in keyword_lower:
            core_value = keyword_lower.split(':', 1)[1].strip()
        
        # Enhanced semantic matching for common patterns
        is_matched = False
        
        # Direct match
        if keyword_lower in response_lower or core_value in response_lower:
            is_matched = True
        
        # Semantic equivalents for "Flow will NOT execute"
        elif 'will not execute' in keyword_lower or 'not execute' in keyword_lower:
            not_execute_variants = [
                'will not execute', 'won\'t execute', 'will **not** execute',
                'will **not execute**', 'does not execute', 'doesn\'t execute',
                'not be executed', 'will not be triggered', 'won\'t be triggered',
                'will not fire', 'won\'t fire', 'will not run', 'won\'t run',
                'not triggered', 'not executed', 'will skip', 'skipped'
            ]
            for variant in not_execute_variants:
                if variant in response_lower:
                    is_matched = True
                    break
        
        # Semantic equivalents for "Requires X = Y" patterns
        elif keyword_lower.startswith('requires '):
            # Extract field and value: "Requires Offer_Name__c = Credit Card"
            req_parts = keyword_lower.replace('requires ', '').split('=')
            if len(req_parts) >= 2:
                field_part = req_parts[0].strip()
                value_part = req_parts[1].strip()
                # Check if both field and value are mentioned in response
                if field_part in response_lower and value_part in response_lower:
                    is_matched = True
                # Also check for variations like "field must be value", "field equalto value"
                elif f"{field_part}" in response_lower and f"{value_part}" in response_lower:
                    is_matched = True
        
        # Check individual significant words from the keyword
        elif len(keyword_lower) > 20:  # For longer expected phrases
            # Split into significant words and check if most are present
            words = [w for w in keyword_lower.split() if len(w) > 3 
                     and w not in ['will', 'the', 'flow', 'that', 'this', 'with', 'from', 'does']]
            if words:
                words_found = sum(1 for w in words if w in response_lower)
                if words_found >= len(words) * 0.7:  # 70% of significant words found
                    is_matched = True
        
        if is_matched:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    # 2. Cross-validate against actual flow metadata (baseline truth)
    metadata_mismatches = []
    inner = flow_metadata.get('Metadata', flow_metadata)
    
    # Extract actual trigger filter values from flow metadata
    start = inner.get('start') or {}
    actual_filters = {}
    for f in start.get('filters', []):
        field = f.get('field', '')
        value_obj = f.get('value', {})
        actual_value = _extract_value(value_obj) if value_obj else None
        operator = f.get('operator', '')
        if field and actual_value is not None:
            actual_filters[field] = {'value': str(actual_value), 'operator': operator}
    
    # Extract actual decision values from flow metadata
    actual_decisions = {}
    for decision in inner.get('decisions', []):
        for rule in decision.get('rules', []):
            for condition in rule.get('conditions', []):
                left = condition.get('leftValueReference', '')
                right_obj = condition.get('rightValue', {})
                right_val = _extract_value(right_obj) if right_obj else None
                operator = condition.get('operator', '')
                if left and right_val is not None:
                    field_name = left.split('.')[-1] if '.' in left else left
                    actual_decisions[field_name] = {'value': str(right_val), 'operator': operator}
    
    # Combine all actual values
    all_actual_values = {**actual_filters, **actual_decisions}
    
    # Check if the scenario's expected values match the baseline
    scenario_context = scenario.get('context', '')
    for field, info in all_actual_values.items():
        actual_val = info['value']
        
        # Check if the scenario itself has wrong data
        if field.lower() in scenario_context.lower():
            # Extract the value from scenario context
            parts = scenario_context.split(field)
            for part in parts[1:]:
                # Look for the value after the field name
                for word in part.split():
                    word_clean = word.strip('.,;:!?()[]{}"\' ')
                    if len(word_clean) > 2 and word_clean.lower() != actual_val.lower():
                        # Check if the scenario has a different value than baseline
                        if word_clean.lower() not in ['equalto', 'notequalto', 'greaterorequal',
                                                       'lessthan', 'contains', 'ischanged',
                                                       'testing', 'trigger', 'condition',
                                                       'the', 'and', 'for', 'what', 'how',
                                                       'does', 'not', 'flow']:
                            # Verify this word is meant to be the value
                            if actual_val.lower() != word_clean.lower() and len(word_clean) > 3:
                                metadata_mismatches.append({
                                    'field': field,
                                    'scenario_value': word_clean,
                                    'baseline_value': actual_val,
                                    'source': 'scenario_context'
                                })
                    break
        
        # Check if AI response mentions wrong values for this field
        if field.lower() in response_lower:
            if actual_val.lower() not in response_lower:
                metadata_mismatches.append({
                    'field': field,
                    'expected_value': actual_val,
                    'source': 'ai_response_missing_correct_value'
                })
    
    # Determine validation status
    keyword_match_pct = (len(matched_keywords) / len(expected) * 100) if expected else 100
    
    if metadata_mismatches:
        status = 'FAIL'
        for mm in metadata_mismatches:
            if mm['source'] == 'scenario_context':
                issues.append(
                    f"⚠️  SCENARIO DATA MISMATCH: Field '{mm['field']}' has "
                    f"'{mm['scenario_value']}' in scenario but baseline says '{mm['baseline_value']}'"
                )
            else:
                issues.append(
                    f"⚠️  AI RESPONSE ISSUE: Field '{mm['field']}' actual value "
                    f"'{mm['expected_value']}' not found in AI response"
                )
    elif keyword_match_pct < 50:
        status = 'FAIL'
        issues.append(f"Only {keyword_match_pct:.0f}% of expected keywords found")
    elif keyword_match_pct < 80:
        status = 'WARN'
        warnings.append(f"{keyword_match_pct:.0f}% keyword match (expected ≥80%)")
    else:
        status = 'PASS'
    
    return {
        'status': status,
        'keyword_match': f"{len(matched_keywords)}/{len(expected)}",
        'keyword_pct': keyword_match_pct,
        'matched': matched_keywords,
        'missing': missing_keywords,
        'metadata_mismatches': metadata_mismatches,
        'issues': issues,
        'warnings': warnings
    }


def _extract_value(value_obj):
    """Extract actual value from Salesforce value object"""
    if not value_obj:
        return None
    if isinstance(value_obj, str):
        return value_obj
    if value_obj.get('stringValue') is not None:
        return value_obj['stringValue']
    elif value_obj.get('numberValue') is not None:
        return str(value_obj['numberValue'])
    elif value_obj.get('booleanValue') is not None:
        return str(value_obj['booleanValue'])
    elif value_obj.get('elementReference'):
        return value_obj['elementReference']
    return None


def main():
    parser = argparse.ArgumentParser(description='Run decision-based test scenarios')
    parser.add_argument('--max', type=int, default=5, help='Maximum scenarios to run')
    parser.add_argument('--category', type=str, help='Run scenarios from specific category')
    parser.add_argument('--flow', type=str, help='Run scenarios for specific flow')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    parser.add_argument('--report', action='store_true', help='Generate HTML report after execution')
    parser.add_argument('--list-categories', action='store_true', help='List available categories')
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              RUN DECISION-BASED TEST SCENARIOS                              ║
║                                                                              ║
║   Testing flow decisions, conditions, thresholds, and logic                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Load scenarios
    data = load_scenarios()
    if not data:
        return
    
    scenarios = data.get('scenarios', [])
    
    if args.list_categories:
        print("📋 Available Categories:\n")
        categories = data.get('categories', [])
        for cat in sorted(categories):
            count = len([s for s in scenarios if s['category'] == cat])
            print(f"   • {cat} ({count} scenarios)")
        return
    
    # Filter scenarios
    if args.category:
        scenarios = [s for s in scenarios if s['category'] == args.category]
        print(f"📂 Filtered to category: {args.category}")
    
    if args.flow:
        scenarios = [s for s in scenarios if s['flow'] == args.flow]
        print(f"📂 Filtered to flow: {args.flow}")
    
    if not args.all:
        scenarios = scenarios[:args.max]
    
    print(f"🧪 Running {len(scenarios)} scenarios...\n")
    
    # Initialize model
    print("🤖 Initializing AI model...")
    model = create_model_from_config()
    print("✅ Model initialized\n")
    
    # Run scenarios
    results = []
    successful = 0
    failed = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{'='*80}")
        print(f"  Scenario {i}/{len(scenarios)}: [{scenario['category']}]")
        print(f"{'='*80}")
        print(f"\n📌 Flow: {scenario['flow']}")
        print(f"❓ Query: {scenario['query']}")
        print(f"📋 Context: {scenario['context']}")
        print()
        
        # Load flow metadata
        flow_metadata = load_flow_from_cache(scenario['flow'])
        
        if not flow_metadata:
            # Try direct file load
            flow_metadata = load_flow(scenario['flow'])
        
        if not flow_metadata:
            print(f"⚠️  Flow metadata not found for: {scenario['flow']}")
            failed += 1
            results.append({
                'scenario': scenario,
                'success': False,
                'error': 'Flow metadata not found'
            })
            continue
        
        # Run the scenario
        print("🔄 Analyzing with baseline flow metadata...")
        result = run_scenario(model, scenario, flow_metadata)
        
        if result['success']:
            validation = result.get('validation', {})
            val_status = validation.get('status', 'UNKNOWN')
            
            print(f"\n📝 AI Analysis:")
            print("-" * 60)
            # Truncate long responses
            response = result['response']
            if len(response) > 1500:
                print(response[:1500] + "\n... [truncated]")
            else:
                print(response)
            print("-" * 60)
            
            # Show validation results
            print(f"\n🔍 VALIDATION AGAINST BASELINE:")
            print(f"   Keywords: {validation.get('keyword_match', 'N/A')} ({validation.get('keyword_pct', 0):.0f}%)")
            
            if val_status == 'PASS':
                successful += 1
                print(f"   ✅ PASS - AI response matches baseline flow data ({result['elapsed_seconds']:.1f}s)")
            elif val_status == 'WARN':
                successful += 1
                print(f"   ⚠️  WARN - Partial match ({result['elapsed_seconds']:.1f}s)")
                for w in validation.get('warnings', []):
                    print(f"      {w}")
            elif val_status == 'FAIL':
                failed += 1
                print(f"   ❌ FAIL - Validation failed ({result['elapsed_seconds']:.1f}s)")
                for issue in validation.get('issues', []):
                    print(f"      {issue}")
            
            if validation.get('missing'):
                print(f"   📋 Missing keywords: {', '.join(validation['missing'][:5])}")
            
            if validation.get('metadata_mismatches'):
                print(f"\n   🔴 BASELINE MISMATCHES DETECTED:")
                for mm in validation['metadata_mismatches']:
                    if mm['source'] == 'scenario_context':
                        print(f"      Field: {mm['field']}")
                        print(f"      Scenario says: {mm['scenario_value']}")
                        print(f"      Baseline says: {mm['baseline_value']}")
                        print(f"      → Scenario data needs correction!")
                    else:
                        print(f"      Field: {mm['field']}")
                        print(f"      Expected: {mm['expected_value']}")
                        print(f"      → AI did not mention the correct value")
        else:
            failed += 1
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        
        results.append({
            'scenario': scenario,
            **result
        })
        print()
    
    # Summary
    print("\n" + "=" * 80)
    print("  RESULTS SUMMARY")
    print("=" * 80)
    
    # Count validation statuses
    pass_count = sum(1 for r in results if r.get('validation', {}).get('status') == 'PASS')
    warn_count = sum(1 for r in results if r.get('validation', {}).get('status') == 'WARN')
    fail_count = sum(1 for r in results if r.get('validation', {}).get('status') == 'FAIL')
    error_count = sum(1 for r in results if not r.get('success'))
    mismatch_count = sum(
        len(r.get('validation', {}).get('metadata_mismatches', []))
        for r in results
    )
    
    print(f"""
📊 Total Scenarios: {len(scenarios)}
✅ Passed (validated against baseline): {pass_count}
⚠️  Warnings (partial match): {warn_count}
❌ Failed (validation mismatch): {fail_count}
� Errors (API/runtime): {error_count}
🔴 Baseline Data Mismatches: {mismatch_count}
📈 Pass Rate: {(pass_count/len(scenarios)*100) if scenarios else 0:.1f}%
""")
    
    # Group results by category
    print("📋 Results by Category:")
    category_results = {}
    for r in results:
        cat = r['scenario']['category']
        if cat not in category_results:
            category_results[cat] = {'success': 0, 'failed': 0}
        if r.get('success'):
            category_results[cat]['success'] += 1
        else:
            category_results[cat]['failed'] += 1
    
    for cat, stats in sorted(category_results.items()):
        total = stats['success'] + stats['failed']
        pct = (stats['success'] / total * 100) if total > 0 else 0
        print(f"   • {cat}: {stats['success']}/{total} ({pct:.0f}%)")
    
    # Save results
    if args.save or args.report:
        results_file = os.path.join(
            PROJECT_ROOT, 
            'data',
            f"decision_scenario_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        results_data = {
            'run_at': datetime.now().isoformat(),
            'total': len(scenarios),
            'successful': successful,
            'failed': failed,
            'pass_count': pass_count,
            'warn_count': warn_count,
            'fail_count': fail_count,
            'error_count': error_count,
            'results': results
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Generate HTML report
        if args.report:
            try:
                from generate_scenario_report import generate_report
                
                report_path = generate_report(results_data)
                print(f"\n📊 HTML Report generated!")
                print(f"   📁 Report: {report_path}")
                print(f"\n   🌐 Open in browser:")
                print(f"      open {report_path}")
                
                # Also show path to latest report
                reports_dir = os.path.join(PROJECT_ROOT, 'reports')
                latest_report = os.path.join(reports_dir, 'latest_report.html')
                print(f"\n   📌 Latest report always at:")
                print(f"      {latest_report}")
            except Exception as e:
                print(f"\n⚠️  Could not generate HTML report: {e}")


if __name__ == "__main__":
    main()

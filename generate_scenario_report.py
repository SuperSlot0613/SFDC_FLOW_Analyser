#!/usr/bin/env python3
"""
Allure-Style Test Report Generator
===================================

Generates beautiful, interactive HTML reports for Salesforce Flow
decision-based scenario test results.

Features:
- Executive Summary Dashboard
- Flow-wise breakdown with pass/fail charts
- Category analysis
- Detailed scenario results with AI responses
- Trend analysis (if historical data available)
- Export-ready format
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any


def generate_report(results_data: Dict, output_dir: str = None) -> str:
    """
    Generate an Allure-style HTML report from test results.
    
    Args:
        results_data: Dictionary containing test results
        output_dir: Directory to save the report (default: reports/)
        
    Returns:
        Path to the generated HTML report
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'reports')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data
    run_at = results_data.get('run_at', datetime.now().isoformat())
    total = results_data.get('total', 0)
    results = results_data.get('results', [])
    
    # Calculate statistics
    stats = calculate_statistics(results)
    
    # Generate HTML
    html_content = generate_html(results_data, stats, run_at)
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(output_dir, f'scenario_report_{timestamp}.html')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Also save as latest report
    latest_file = os.path.join(output_dir, 'latest_report.html')
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_file


def calculate_statistics(results: List[Dict]) -> Dict:
    """Calculate comprehensive statistics from results."""
    stats = {
        'total': len(results),
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'errors': 0,
        'by_flow': {},
        'by_category': {},
        'avg_response_time': 0,
        'total_response_time': 0,
        'baseline_mismatches': 0,
        'keyword_coverage': [],
        'flows_tested': set(),
        'categories_tested': set()
    }
    
    total_time = 0
    time_count = 0
    
    for result in results:
        scenario = result.get('scenario', {})
        flow = scenario.get('flow', 'Unknown')
        category = scenario.get('category', 'Unknown')
        validation = result.get('validation', {})
        status = validation.get('status', 'ERROR')
        
        stats['flows_tested'].add(flow)
        stats['categories_tested'].add(category)
        
        # Initialize flow stats
        if flow not in stats['by_flow']:
            stats['by_flow'][flow] = {
                'total': 0, 'passed': 0, 'failed': 0, 
                'warnings': 0, 'errors': 0, 'scenarios': []
            }
        
        # Initialize category stats
        if category not in stats['by_category']:
            stats['by_category'][category] = {
                'total': 0, 'passed': 0, 'failed': 0,
                'warnings': 0, 'errors': 0
            }
        
        # Count by status
        if not result.get('success'):
            stats['errors'] += 1
            stats['by_flow'][flow]['errors'] += 1
            stats['by_category'][category]['errors'] += 1
        elif status == 'PASS':
            stats['passed'] += 1
            stats['by_flow'][flow]['passed'] += 1
            stats['by_category'][category]['passed'] += 1
        elif status == 'WARN':
            stats['warnings'] += 1
            stats['by_flow'][flow]['warnings'] += 1
            stats['by_category'][category]['warnings'] += 1
        else:
            stats['failed'] += 1
            stats['by_flow'][flow]['failed'] += 1
            stats['by_category'][category]['failed'] += 1
        
        stats['by_flow'][flow]['total'] += 1
        stats['by_category'][category]['total'] += 1
        stats['by_flow'][flow]['scenarios'].append(result)
        
        # Response time
        elapsed = result.get('elapsed_seconds', 0)
        if elapsed > 0:
            total_time += elapsed
            time_count += 1
        
        # Baseline mismatches
        mismatches = validation.get('metadata_mismatches', [])
        stats['baseline_mismatches'] += len(mismatches)
        
        # Keyword coverage
        keyword_pct = validation.get('keyword_pct', 0)
        stats['keyword_coverage'].append(keyword_pct)
    
    stats['avg_response_time'] = total_time / time_count if time_count > 0 else 0
    stats['total_response_time'] = total_time
    stats['flows_tested'] = list(stats['flows_tested'])
    stats['categories_tested'] = list(stats['categories_tested'])
    stats['avg_keyword_coverage'] = (
        sum(stats['keyword_coverage']) / len(stats['keyword_coverage'])
        if stats['keyword_coverage'] else 0
    )
    
    return stats


def generate_html(results_data: Dict, stats: Dict, run_at: str) -> str:
    """Generate the complete HTML report."""
    
    # Calculate pass rate
    pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    # Generate flow cards
    flow_cards_html = generate_flow_cards(stats['by_flow'])
    
    # Generate category breakdown
    category_html = generate_category_breakdown(stats['by_category'])
    
    # Generate detailed results
    details_html = generate_detailed_results(results_data.get('results', []))
    
    # Generate flow chart data
    flow_chart_data = json.dumps({
        'labels': list(stats['by_flow'].keys()),
        'passed': [f['passed'] for f in stats['by_flow'].values()],
        'failed': [f['failed'] for f in stats['by_flow'].values()],
        'warnings': [f['warnings'] for f in stats['by_flow'].values()],
        'errors': [f['errors'] for f in stats['by_flow'].values()]
    })
    
    # Determine overall status color
    if pass_rate >= 80:
        status_color = '#28a745'
        status_text = 'HEALTHY'
    elif pass_rate >= 50:
        status_color = '#ffc107'
        status_text = 'NEEDS ATTENTION'
    else:
        status_color = '#dc3545'
        status_text = 'CRITICAL'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flow Scenario Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #0176d3;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
            --dark: #343a40;
            --light: #f8f9fa;
            --border: #dee2e6;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .logo-icon {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
        }}
        
        .logo-text h1 {{
            font-size: 24px;
            color: var(--dark);
        }}
        
        .logo-text p {{
            color: #666;
            font-size: 14px;
        }}
        
        .run-info {{
            text-align: right;
            color: #666;
            font-size: 14px;
        }}
        
        .run-info strong {{
            color: var(--dark);
        }}
        
        /* Status Banner */
        .status-banner {{
            background: {status_color};
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .status-badge {{
            font-size: 18px;
            font-weight: bold;
        }}
        
        .pass-rate {{
            font-size: 32px;
            font-weight: bold;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card.passed {{ border-left: 4px solid var(--success); }}
        .stat-card.failed {{ border-left: 4px solid var(--danger); }}
        .stat-card.warnings {{ border-left: 4px solid var(--warning); }}
        .stat-card.errors {{ border-left: 4px solid var(--info); }}
        .stat-card.time {{ border-left: 4px solid var(--primary); }}
        .stat-card.coverage {{ border-left: 4px solid #6f42c1; }}
        
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: var(--dark);
        }}
        
        .stat-label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .stat-icon {{
            float: right;
            font-size: 24px;
            opacity: 0.3;
        }}
        
        /* Charts Section */
        .charts-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        @media (max-width: 900px) {{
            .charts-section {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        
        .chart-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--dark);
        }}
        
        /* Flow Cards */
        .flow-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .flow-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .flow-card {{
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }}
        
        .flow-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 5px 20px rgba(1, 118, 211, 0.15);
        }}
        
        .flow-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .flow-name {{
            font-weight: 600;
            color: var(--dark);
            font-size: 16px;
        }}
        
        .flow-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .flow-badge.success {{ background: #d4edda; color: #155724; }}
        .flow-badge.warning {{ background: #fff3cd; color: #856404; }}
        .flow-badge.danger {{ background: #f8d7da; color: #721c24; }}
        
        .flow-stats {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .flow-stat {{
            text-align: center;
        }}
        
        .flow-stat-value {{
            font-size: 20px;
            font-weight: bold;
        }}
        
        .flow-stat-value.pass {{ color: var(--success); }}
        .flow-stat-value.fail {{ color: var(--danger); }}
        .flow-stat-value.warn {{ color: var(--warning); }}
        
        .flow-stat-label {{
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
        }}
        
        .flow-progress {{
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .flow-progress-bar {{
            height: 100%;
            transition: width 0.5s ease;
        }}
        
        .flow-progress-bar.pass {{ background: var(--success); }}
        .flow-progress-bar.warn {{ background: var(--warning); }}
        .flow-progress-bar.fail {{ background: var(--danger); }}
        
        /* Category Section */
        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .category-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: var(--light);
            border-radius: 8px;
        }}
        
        .category-name {{
            font-weight: 500;
            color: var(--dark);
        }}
        
        .category-stats {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .category-count {{
            font-size: 14px;
            padding: 2px 8px;
            border-radius: 12px;
        }}
        
        .category-count.pass {{ background: #d4edda; color: #155724; }}
        .category-count.fail {{ background: #f8d7da; color: #721c24; }}
        
        /* Details Section */
        .details-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        
        .scenario-accordion {{
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 10px;
            overflow: hidden;
        }}
        
        .scenario-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: var(--light);
            cursor: pointer;
            transition: background 0.3s ease;
        }}
        
        .scenario-header:hover {{
            background: #e9ecef;
        }}
        
        .scenario-header.pass {{ border-left: 4px solid var(--success); }}
        .scenario-header.fail {{ border-left: 4px solid var(--danger); }}
        .scenario-header.warn {{ border-left: 4px solid var(--warning); }}
        .scenario-header.error {{ border-left: 4px solid var(--info); }}
        
        .scenario-title {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .scenario-status {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .scenario-status.pass {{ background: var(--success); }}
        .scenario-status.fail {{ background: var(--danger); }}
        .scenario-status.warn {{ background: var(--warning); }}
        .scenario-status.error {{ background: var(--info); }}
        
        .scenario-name {{
            font-weight: 500;
            color: var(--dark);
        }}
        
        .scenario-meta {{
            display: flex;
            gap: 15px;
            align-items: center;
            font-size: 13px;
            color: #666;
        }}
        
        .scenario-body {{
            display: none;
            padding: 20px;
            border-top: 1px solid var(--border);
        }}
        
        .scenario-body.active {{
            display: block;
        }}
        
        .scenario-query {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            color: var(--dark);
        }}
        
        .scenario-response {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .validation-info {{
            margin-top: 15px;
            padding: 15px;
            background: var(--light);
            border-radius: 8px;
        }}
        
        .validation-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .validation-row:last-child {{
            border-bottom: none;
        }}
        
        .keyword-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 10px;
        }}
        
        .keyword-tag {{
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
        }}
        
        .keyword-tag.matched {{ background: #d4edda; color: #155724; }}
        .keyword-tag.missing {{ background: #f8d7da; color: #721c24; }}
        
        /* Filter Controls */
        .filter-controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: white;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 13px;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-size: 14px;
        }}
        
        .footer a {{
            color: white;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .animate-in {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                max-width: 100%;
            }}
            .scenario-body {{
                display: block !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header animate-in">
            <div class="header-top">
                <div class="logo">
                    <div class="logo-icon">⚡</div>
                    <div class="logo-text">
                        <h1>Flow Scenario Test Report</h1>
                        <p>Salesforce Flow Decision-Based Analysis</p>
                    </div>
                </div>
                <div class="run-info">
                    <div>Run: <strong>{run_at[:19].replace('T', ' ')}</strong></div>
                    <div>Generated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></div>
                </div>
            </div>
            <div class="status-banner">
                <div class="status-badge">🎯 {status_text}</div>
                <div class="pass-rate">{pass_rate:.1f}% Pass Rate</div>
            </div>
        </header>
        
        <!-- Stats Grid -->
        <div class="stats-grid animate-in" style="animation-delay: 0.1s;">
            <div class="stat-card passed">
                <span class="stat-icon">✅</span>
                <div class="stat-value">{stats['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card failed">
                <span class="stat-icon">❌</span>
                <div class="stat-value">{stats['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card warnings">
                <span class="stat-icon">⚠️</span>
                <div class="stat-value">{stats['warnings']}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card errors">
                <span class="stat-icon">💥</span>
                <div class="stat-value">{stats['errors']}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card time">
                <span class="stat-icon">⏱️</span>
                <div class="stat-value">{stats['avg_response_time']:.1f}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
            <div class="stat-card coverage">
                <span class="stat-icon">📊</span>
                <div class="stat-value">{stats['avg_keyword_coverage']:.0f}%</div>
                <div class="stat-label">Keyword Coverage</div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="charts-section animate-in" style="animation-delay: 0.2s;">
            <div class="chart-card">
                <div class="chart-title">📊 Results Distribution</div>
                <canvas id="resultsChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">📈 Results by Flow</div>
                <canvas id="flowChart"></canvas>
            </div>
        </div>
        
        <!-- Flow Breakdown -->
        <div class="flow-section animate-in" style="animation-delay: 0.3s;">
            <div class="section-title">🔄 Flow-wise Breakdown</div>
            <div class="flow-grid">
                {flow_cards_html}
            </div>
        </div>
        
        <!-- Category Breakdown -->
        <div class="flow-section animate-in" style="animation-delay: 0.4s;">
            <div class="section-title">📁 Category Analysis</div>
            <div class="category-grid">
                {category_html}
            </div>
        </div>
        
        <!-- Detailed Results -->
        <div class="details-section animate-in" style="animation-delay: 0.5s;">
            <div class="section-title">📋 Detailed Scenario Results</div>
            <div class="filter-controls">
                <button class="filter-btn active" onclick="filterScenarios('all')">All ({stats['total']})</button>
                <button class="filter-btn" onclick="filterScenarios('pass')">✅ Passed ({stats['passed']})</button>
                <button class="filter-btn" onclick="filterScenarios('fail')">❌ Failed ({stats['failed']})</button>
                <button class="filter-btn" onclick="filterScenarios('warn')">⚠️ Warnings ({stats['warnings']})</button>
                <button class="filter-btn" onclick="filterScenarios('error')">💥 Errors ({stats['errors']})</button>
            </div>
            <div id="scenarioList">
                {details_html}
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="footer">
            <p>Generated by <strong>Salesforce Flow AI Implementation</strong></p>
            <p>Total Execution Time: {stats['total_response_time']:.1f}s | Flows Tested: {len(stats['flows_tested'])} | Categories: {len(stats['categories_tested'])}</p>
        </footer>
    </div>
    
    <script>
        // Results Distribution Chart
        const resultsCtx = document.getElementById('resultsChart').getContext('2d');
        new Chart(resultsCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Warnings', 'Errors'],
                datasets: [{{
                    data: [{stats['passed']}, {stats['failed']}, {stats['warnings']}, {stats['errors']}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }},
                cutout: '60%'
            }}
        }});
        
        // Flow Results Chart
        const flowData = {flow_chart_data};
        const flowCtx = document.getElementById('flowChart').getContext('2d');
        new Chart(flowCtx, {{
            type: 'bar',
            data: {{
                labels: flowData.labels.map(l => l.length > 20 ? l.substring(0, 20) + '...' : l),
                datasets: [
                    {{
                        label: 'Passed',
                        data: flowData.passed,
                        backgroundColor: '#28a745'
                    }},
                    {{
                        label: 'Failed',
                        data: flowData.failed,
                        backgroundColor: '#dc3545'
                    }},
                    {{
                        label: 'Warnings',
                        data: flowData.warnings,
                        backgroundColor: '#ffc107'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{
                        stacked: true
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Toggle scenario details
        function toggleScenario(id) {{
            const body = document.getElementById('body-' + id);
            body.classList.toggle('active');
        }}
        
        // Filter scenarios
        function filterScenarios(status) {{
            const items = document.querySelectorAll('.scenario-accordion');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            items.forEach(item => {{
                if (status === 'all') {{
                    item.style.display = 'block';
                }} else {{
                    if (item.classList.contains('status-' + status)) {{
                        item.style.display = 'block';
                    }} else {{
                        item.style.display = 'none';
                    }}
                }}
            }});
        }}
        
        // Expand all
        function expandAll() {{
            document.querySelectorAll('.scenario-body').forEach(body => {{
                body.classList.add('active');
            }});
        }}
        
        // Collapse all
        function collapseAll() {{
            document.querySelectorAll('.scenario-body').forEach(body => {{
                body.classList.remove('active');
            }});
        }}
    </script>
</body>
</html>'''
    
    return html


def generate_flow_cards(by_flow: Dict) -> str:
    """Generate HTML for flow cards."""
    cards = []
    
    for flow_name, data in sorted(by_flow.items()):
        total = data['total']
        passed = data['passed']
        failed = data['failed']
        warnings = data['warnings']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Determine badge
        if pass_rate >= 80:
            badge_class = 'success'
            badge_text = f'{pass_rate:.0f}% Pass'
        elif pass_rate >= 50:
            badge_class = 'warning'
            badge_text = f'{pass_rate:.0f}% Pass'
        else:
            badge_class = 'danger'
            badge_text = f'{pass_rate:.0f}% Pass'
        
        # Calculate progress widths
        pass_width = (passed / total * 100) if total > 0 else 0
        warn_width = (warnings / total * 100) if total > 0 else 0
        fail_width = ((failed + data['errors']) / total * 100) if total > 0 else 0
        
        # Truncate long flow names
        display_name = flow_name if len(flow_name) <= 35 else flow_name[:32] + '...'
        
        card = f'''
        <div class="flow-card">
            <div class="flow-header">
                <div class="flow-name" title="{flow_name}">{display_name}</div>
                <span class="flow-badge {badge_class}">{badge_text}</span>
            </div>
            <div class="flow-stats">
                <div class="flow-stat">
                    <div class="flow-stat-value pass">{passed}</div>
                    <div class="flow-stat-label">Passed</div>
                </div>
                <div class="flow-stat">
                    <div class="flow-stat-value warn">{warnings}</div>
                    <div class="flow-stat-label">Warnings</div>
                </div>
                <div class="flow-stat">
                    <div class="flow-stat-value fail">{failed}</div>
                    <div class="flow-stat-label">Failed</div>
                </div>
                <div class="flow-stat">
                    <div class="flow-stat-value" style="color: #17a2b8;">{data['errors']}</div>
                    <div class="flow-stat-label">Errors</div>
                </div>
            </div>
            <div class="flow-progress">
                <div class="flow-progress-bar pass" style="width: {pass_width}%; display: inline-block;"></div>
                <div class="flow-progress-bar warn" style="width: {warn_width}%; display: inline-block;"></div>
                <div class="flow-progress-bar fail" style="width: {fail_width}%; display: inline-block;"></div>
            </div>
        </div>
        '''
        cards.append(card)
    
    return '\n'.join(cards)


def generate_category_breakdown(by_category: Dict) -> str:
    """Generate HTML for category breakdown."""
    items = []
    
    for cat_name, data in sorted(by_category.items()):
        total = data['total']
        passed = data['passed']
        failed = data['failed'] + data['errors']
        
        item = f'''
        <div class="category-item">
            <div class="category-name">{cat_name}</div>
            <div class="category-stats">
                <span class="category-count pass">✅ {passed}</span>
                <span class="category-count fail">❌ {failed}</span>
            </div>
        </div>
        '''
        items.append(item)
    
    return '\n'.join(items)


def generate_detailed_results(results: List[Dict]) -> str:
    """Generate HTML for detailed scenario results."""
    items = []
    
    for i, result in enumerate(results):
        scenario = result.get('scenario', {})
        validation = result.get('validation', {})
        status = validation.get('status', 'ERROR') if result.get('success') else 'ERROR'
        
        # Status class
        status_lower = status.lower()
        if not result.get('success'):
            status_lower = 'error'
        
        # Scenario info
        flow_name = scenario.get('flow', 'Unknown')
        category = scenario.get('category', 'Unknown')
        query = scenario.get('query', '')
        context = scenario.get('context', '')
        
        # Response
        response = result.get('response', result.get('error', 'No response'))
        if len(response) > 2000:
            response = response[:2000] + '\n\n... [truncated]'
        
        # Escape HTML in response
        response = response.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Timing
        elapsed = result.get('elapsed_seconds', 0)
        
        # Keywords
        matched = validation.get('matched', [])
        missing = validation.get('missing', [])
        keyword_pct = validation.get('keyword_pct', 0)
        
        matched_tags = ''.join([f'<span class="keyword-tag matched">{k}</span>' for k in matched[:5]])
        missing_tags = ''.join([f'<span class="keyword-tag missing">{k}</span>' for k in missing[:5]])
        
        # Issues
        issues_html = ''
        for issue in validation.get('issues', [])[:3]:
            issues_html += f'<div style="color: #dc3545; margin: 5px 0;">⚠️ {issue}</div>'
        
        item = f'''
        <div class="scenario-accordion status-{status_lower}">
            <div class="scenario-header {status_lower}" onclick="toggleScenario({i})">
                <div class="scenario-title">
                    <span class="scenario-status {status_lower}"></span>
                    <span class="scenario-name">{scenario.get('id', f'Scenario {i+1}')}</span>
                </div>
                <div class="scenario-meta">
                    <span>🔄 {flow_name}</span>
                    <span>📁 {category}</span>
                    <span>⏱️ {elapsed:.1f}s</span>
                    <span>📊 {keyword_pct:.0f}%</span>
                </div>
            </div>
            <div class="scenario-body" id="body-{i}">
                <div style="margin-bottom: 15px;">
                    <strong>Query:</strong>
                    <div class="scenario-query">{query}</div>
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>Context:</strong> {context}
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>AI Response:</strong>
                    <div class="scenario-response">{response}</div>
                </div>
                <div class="validation-info">
                    <div class="validation-row">
                        <span>Status</span>
                        <span><strong>{status}</strong></span>
                    </div>
                    <div class="validation-row">
                        <span>Keyword Match</span>
                        <span>{validation.get('keyword_match', 'N/A')} ({keyword_pct:.0f}%)</span>
                    </div>
                    <div class="validation-row">
                        <span>Response Time</span>
                        <span>{elapsed:.2f} seconds</span>
                    </div>
                    {issues_html}
                    <div style="margin-top: 10px;">
                        <strong>Matched Keywords:</strong>
                        <div class="keyword-tags">{matched_tags if matched_tags else '<span style="color: #666;">None</span>'}</div>
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>Missing Keywords:</strong>
                        <div class="keyword-tags">{missing_tags if missing_tags else '<span style="color: #666;">None</span>'}</div>
                    </div>
                </div>
            </div>
        </div>
        '''
        items.append(item)
    
    return '\n'.join(items)


def load_and_generate_report(results_file: str = None, output_dir: str = None) -> str:
    """
    Load results from file and generate report.
    
    Args:
        results_file: Path to results JSON file (default: latest results file)
        output_dir: Output directory for report
        
    Returns:
        Path to generated report
    """
    base_dir = os.path.dirname(__file__)
    
    # Find latest results file if not specified
    if results_file is None:
        results_files = [
            f for f in os.listdir(base_dir) 
            if f.startswith('decision_scenario_results_') and f.endswith('.json')
        ]
        if results_files:
            results_file = os.path.join(base_dir, sorted(results_files)[-1])
        else:
            print("❌ No results file found. Run scenarios first.")
            return None
    
    # Load results
    with open(results_file, 'r') as f:
        results_data = json.load(f)
    
    # Generate report
    report_path = generate_report(results_data, output_dir)
    
    return report_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Allure-style test report')
    parser.add_argument('--results', type=str, help='Path to results JSON file')
    parser.add_argument('--output', type=str, help='Output directory for report')
    args = parser.parse_args()
    
    report_path = load_and_generate_report(args.results, args.output)
    
    if report_path:
        print(f"\n✅ Report generated: {report_path}")
        print(f"\n📂 Open in browser:")
        print(f"   open {report_path}")

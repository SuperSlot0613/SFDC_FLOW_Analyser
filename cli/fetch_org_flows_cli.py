#!/usr/bin/env python3
"""
Fetch Real Flow Metadata from Salesforce Org using SF CLI
==========================================================

This script uses the Salesforce CLI authentication to fetch flows.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

# Add parent directory and src to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.baseline_manager import BaselineManager
from src.model import create_model_from_config


def get_sf_cli_auth(username=None):
    """Get authentication from Salesforce CLI"""
    print("🔐 Getting authentication from Salesforce CLI...")
    
    try:
        cmd = ['sf', 'org', 'display', '--json']
        if username:
            cmd.extend(['--target-org', username])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ SF CLI error: {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        org_info = data.get('result', {})
        
        if not org_info.get('accessToken'):
            print("❌ No access token found. Please authenticate with: sf org login web")
            return None
        
        print(f"✅ Authenticated to: {org_info.get('instanceUrl')}")
        print(f"   Username: {org_info.get('username')}")
        
        return {
            'access_token': org_info['accessToken'],
            'instance_url': org_info['instanceUrl'],
            'username': org_info.get('username')
        }
        
    except subprocess.TimeoutExpired:
        print("❌ SF CLI timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def fetch_all_flows(auth):
    """Fetch all Flow metadata from Salesforce using Tooling API"""
    print("\n📥 Fetching Flow definitions from Salesforce...")
    
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    # Query to get all flow definitions
    query = """
    SELECT Id, DeveloperName, MasterLabel, Description, ActiveVersionId
    FROM FlowDefinition
    ORDER BY MasterLabel
    """
    
    encoded_query = urllib.parse.quote(query.strip())
    url = f"{instance_url}/services/data/v59.0/tooling/query?q={encoded_query}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        flows = result.get('records', [])
        print(f"✅ Found {len(flows)} flow definitions")
        return flows
        
    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code}")
        error_body = e.read().decode('utf-8')
        print(f"   {error_body[:200]}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def fetch_flow_metadata(auth, flow_id):
    """Fetch detailed metadata for a specific flow"""
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    url = f"{instance_url}/services/data/v59.0/tooling/sobjects/Flow/{flow_id}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None


def fetch_active_flows(auth):
    """Fetch all active Flow versions with their metadata"""
    print("\n📥 Fetching active Flow versions with metadata...")
    
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    # Query active flows with metadata
    query = """
    SELECT Id, Definition.DeveloperName, MasterLabel, VersionNumber, 
           Status, ProcessType, TriggerType, ApiVersion, Description,
           Metadata
    FROM Flow
    WHERE Status = 'Active'
    ORDER BY MasterLabel
    """
    
    encoded_query = urllib.parse.quote(query.strip())
    url = f"{instance_url}/services/data/v59.0/tooling/query?q={encoded_query}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        flows = result.get('records', [])
        print(f"✅ Found {len(flows)} active flows with metadata")
        return flows
        
    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code}")
        error_body = e.read().decode('utf-8')
        print(f"   {error_body[:300]}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         FETCH REAL FLOW METADATA FROM YOUR SALESFORCE ORG                   ║
║                       (Using Salesforce CLI)                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Get authentication from SF CLI
    print("=" * 80)
    print("  STEP 1: Authenticate via Salesforce CLI")
    print("=" * 80)
    
    # Try to use the medisale org
    auth = get_sf_cli_auth("saurabh@medisale.com")
    
    if not auth:
        print("\n⚠️  Please authenticate with Salesforce CLI:")
        print("   sf org login web -a myorg")
        return
    
    # Step 2: Fetch all active flows
    print()
    print("=" * 80)
    print("  STEP 2: Fetch Active Flows")
    print("=" * 80)
    
    flows = fetch_active_flows(auth)
    
    if not flows:
        # Try fetching flow definitions instead
        print("   Trying alternative method...")
        flow_defs = fetch_all_flows(auth)
        
        if flow_defs:
            print(f"\n📋 Flow Definitions Found:")
            for i, fd in enumerate(flow_defs, 1):
                print(f"   {i}. {fd.get('MasterLabel')} (ID: {fd.get('ActiveVersionId', 'No active version')})")
            
            # Fetch metadata for each active version
            flows = []
            for fd in flow_defs:
                active_id = fd.get('ActiveVersionId')
                if active_id:
                    print(f"   Fetching: {fd.get('MasterLabel')}...", end=" ")
                    metadata = fetch_flow_metadata(auth, active_id)
                    if metadata:
                        flows.append(metadata)
                        print("✅")
                    else:
                        print("⚠️")
    
    if not flows:
        print("⚠️  No flows found in your org")
        return
    
    # Display flows
    print(f"\n📋 Flows Retrieved from Your Org:")
    for i, flow in enumerate(flows, 1):
        label = flow.get('MasterLabel', flow.get('Definition', {}).get('DeveloperName', 'Unknown'))
        ptype = flow.get('ProcessType', 'Unknown')
        status = flow.get('Status', 'Unknown')
        print(f"   {i}. [{status}] {label} ({ptype})")
    
    # Step 3: Save flows
    print()
    print("=" * 80)
    print("  STEP 3: Save Flow Metadata")
    print("=" * 80)
    
    output_dir = os.path.join(PROJECT_ROOT, 'org_flows')
    os.makedirs(output_dir, exist_ok=True)
    
    detailed_flows = []
    for flow in flows:
        dev_name = flow.get('Definition', {}).get('DeveloperName') or flow.get('FullName') or f"Flow_{flow.get('Id', 'unknown')}"
        
        flow_data = {
            'Id': flow.get('Id'),
            'FullName': dev_name,
            'MasterLabel': flow.get('MasterLabel', dev_name),
            'Metadata': flow.get('Metadata', {}),
            'ProcessType': flow.get('ProcessType'),
            'TriggerType': flow.get('TriggerType'),
            'Status': flow.get('Status'),
            'ApiVersion': flow.get('ApiVersion'),
            'VersionNumber': flow.get('VersionNumber'),
            'Description': flow.get('Description')
        }
        detailed_flows.append(flow_data)
        
        # Save individual file
        flow_file = os.path.join(output_dir, f"{dev_name}.json")
        with open(flow_file, 'w') as f:
            json.dump(flow_data, f, indent=2, default=str)
    
    # Save combined file
    all_flows_file = os.path.join(output_dir, '_all_flows.json')
    with open(all_flows_file, 'w') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'instance_url': auth['instance_url'],
            'username': auth['username'],
            'flow_count': len(detailed_flows),
            'flows': detailed_flows
        }, f, indent=2, default=str)
    
    print(f"✅ Saved {len(detailed_flows)} flows to: {output_dir}/")
    
    # Step 4: Create baseline
    print()
    print("=" * 80)
    print("  STEP 4: Create Baseline")
    print("=" * 80)
    
    storage_path = os.path.join(os.path.dirname(__file__), 'flow_baselines')
    baseline_manager = BaselineManager(storage_path)
    
    flows_metadata = []
    analysis_results = []
    
    for flow in detailed_flows:
        flows_metadata.append({
            'Id': flow.get('Id'),
            'FullName': flow.get('FullName'),
            'Metadata': flow.get('Metadata', {})
        })
        analysis_results.append({
            'analyzed_at': datetime.now().isoformat(),
            'process_type': flow.get('ProcessType'),
            'status': flow.get('Status'),
            'source': 'salesforce_org'
        })
    
    baseline_metadata = baseline_manager.create_baseline(
        flows_metadata=flows_metadata,
        analysis_results=analysis_results,
        name=f"Org Baseline {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        description=f"Baseline from {auth['instance_url']}",
        created_by=auth['username']
    )
    
    print(f"✅ Baseline created: {baseline_metadata.id}")
    print(f"   Flows: {baseline_metadata.flow_count}")
    
    # Step 5: Test with AI Model
    print()
    print("=" * 80)
    print("  STEP 5: Test AI Analysis on Your Flows")
    print("=" * 80)
    
    if detailed_flows:
        print("\n🤖 Initializing AI Model...")
        model = create_model_from_config()
        
        # Pick the first flow with metadata
        test_flow = None
        for flow in detailed_flows:
            if flow.get('Metadata'):
                test_flow = flow
                break
        
        if test_flow and model.llm_client:
            print(f"\n📝 Testing query on: {test_flow.get('MasterLabel')}")
            print("-" * 60)
            
            try:
                answer = model.query(
                    f"What does the {test_flow.get('MasterLabel')} flow do? Explain its purpose and logic.",
                    context_metadata=test_flow
                )
                print(f"\n{answer[:800]}..." if len(answer) > 800 else f"\n{answer}")
            except Exception as e:
                print(f"⚠️  Query error: {e}")
    
    # Summary
    print()
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    # Group by type
    flow_types = {}
    for flow in detailed_flows:
        ptype = flow.get('ProcessType', 'Unknown')
        flow_types[ptype] = flow_types.get(ptype, 0) + 1
    
    print(f"""
✅ Successfully fetched flows from your Salesforce org!

📊 Org Details:
   Instance: {auth['instance_url']}
   Username: {auth['username']}

📦 Flows Retrieved: {len(detailed_flows)}
""")
    
    print("📋 Flows by Type:")
    for ptype, count in sorted(flow_types.items()):
        print(f"   • {ptype}: {count}")
    
    print(f"""
💾 Files Created:
   • org_flows/*.json (individual flow files)
   • org_flows/_all_flows.json (combined)
   • flow_baselines/ (baseline data)

🚀 Next Steps:
   1. Query your flows: python -c "from src.model import *; m=create_model_from_config(); print(m.query('What does flow X do?'))"
   2. Run regression tests: python demo_regression.py
   3. Run scenario tests: python run_scenario_tests.py
""")


if __name__ == "__main__":
    main()

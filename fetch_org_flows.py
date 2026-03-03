#!/usr/bin/env python3
"""
Fetch Real Flow Metadata from Salesforce Org
=============================================

This script connects to your Salesforce org using the credentials in .env
and fetches all Flow metadata to create a baseline.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import init_config
from baseline_manager import BaselineManager


def authenticate_salesforce(config):
    """
    Authenticate to Salesforce using OAuth Password Flow
    """
    print("🔐 Authenticating to Salesforce...")
    
    sf_config = config.salesforce
    
    # Check if we have a direct access token
    if sf_config.access_token:
        print("✅ Using direct access token")
        return {
            'access_token': sf_config.access_token,
            'instance_url': sf_config.instance_url
        }
    
    # Try OAuth Password Flow - use login.salesforce.com for production or test.salesforce.com for sandbox
    # This will automatically redirect to the correct instance
    token_url = "https://login.salesforce.com/services/oauth2/token"
    
    # Build password with security token
    password = sf_config.password
    if sf_config.security_token:
        password = password + sf_config.security_token

    print(f"   Client ID: {sf_config.client_id}")
    print(f"   Username: {sf_config.username}")
    print(f"   Password: {password}")

    params = {
        'grant_type': 'password',
        'client_id': sf_config.client_id,
        'client_secret': sf_config.client_secret,
        'username': sf_config.username,
        'password': password
    }
    
    data = urllib.parse.urlencode(params).encode('utf-8')
    
    try:
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        print(f"✅ Authentication successful!")
        print(f"   Instance: {result.get('instance_url')}")
        
        return {
            'access_token': result['access_token'],
            'instance_url': result['instance_url']
        }
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Authentication failed: {e.code}")
        print(f"   Error: {error_body}")
        
        # Try to parse error
        try:
            error_json = json.loads(error_body)
            if 'error_description' in error_json:
                print(f"   Description: {error_json['error_description']}")
        except:
            pass
            
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def fetch_all_flows(auth):
    """
    Fetch all Flow metadata from Salesforce using Tooling API
    """
    print("\n📥 Fetching Flow metadata from Salesforce...")
    
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    # Query to get all flows
    query = """
    SELECT Id, DeveloperName, MasterLabel, Description, ProcessType, 
           TriggerType, ApiVersion, Status, LastModifiedDate, 
           LastModifiedById, CreatedDate
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
        print(f"✅ Found {len(flows)} flows in your org")
        
        return flows
        
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to fetch flows: {e.code}")
        error_body = e.read().decode('utf-8')
        print(f"   Error: {error_body}")
        return []
    except Exception as e:
        print(f"❌ Error fetching flows: {e}")
        return []


def fetch_flow_versions(auth, flow_definition_id):
    """
    Fetch all versions of a specific flow
    """
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    query = f"""
    SELECT Id, FlowDefinitionId, VersionNumber, Status, ApiVersion
    FROM FlowVersionView
    WHERE FlowDefinitionId = '{flow_definition_id}'
    ORDER BY VersionNumber DESC
    LIMIT 1
    """
    
    encoded_query = urllib.parse.quote(query.strip())
    url = f"{instance_url}/services/data/v59.0/tooling/query?q={encoded_query}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        return result.get('records', [])
    except:
        return []


def fetch_flow_metadata(auth, flow_id):
    """
    Fetch detailed metadata for a specific flow using its ID
    """
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    url = f"{instance_url}/services/data/v59.0/tooling/sobjects/Flow/{flow_id}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        return None


def fetch_active_flow_metadata(auth, developer_name):
    """
    Fetch the active version metadata for a flow by developer name
    """
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    # First get the active flow ID
    query = f"""
    SELECT Id, Definition.DeveloperName, VersionNumber, Status, 
           ProcessType, TriggerType, ApiVersion, Metadata
    FROM Flow
    WHERE Definition.DeveloperName = '{developer_name}'
    AND Status = 'Active'
    LIMIT 1
    """
    
    encoded_query = urllib.parse.quote(query.strip())
    url = f"{instance_url}/services/data/v59.0/tooling/query?q={encoded_query}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        records = result.get('records', [])
        if records:
            return records[0]
        return None
        
    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        return None


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         FETCH REAL FLOW METADATA FROM YOUR SALESFORCE ORG                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Load configuration
    print("=" * 80)
    print("  STEP 1: Load Configuration")
    print("=" * 80)
    
    config = init_config()
    
    if not config.salesforce.client_id:
        print("❌ Salesforce credentials not configured in .env")
        print("   Please add SF_CLIENT_ID, SF_CLIENT_SECRET, SF_USERNAME, SF_PASSWORD")
        return
    
    print(f"✅ Salesforce configured:")
    print(f"   Instance: {config.salesforce.instance_url}")
    print(f"   Username: {config.salesforce.username}")
    
    # Step 2: Authenticate
    print()
    print("=" * 80)
    print("  STEP 2: Authenticate to Salesforce")
    print("=" * 80)
    
    auth = authenticate_salesforce(config)
    
    if not auth:
        print("\n⚠️  Cannot connect to Salesforce.")
        print("   Please check your credentials in .env file.")
        print("\n   Common issues:")
        print("   - Password may need security token appended")
        print("   - Connected App may not be configured for OAuth")
        print("   - IP restrictions on Connected App")
        return
    
    # Step 3: Fetch all flows
    print()
    print("=" * 80)
    print("  STEP 3: Fetch All Flows")
    print("=" * 80)
    
    flows = fetch_all_flows(auth)
    
    if not flows:
        print("⚠️  No flows found in your org (or unable to fetch)")
        return
    
    # Display found flows
    print(f"\n📋 Flows found in your org:")
    for i, flow in enumerate(flows, 1):
        status = flow.get('Status', 'Unknown')
        status_emoji = "✅" if status == "Active" else "⏸️"
        print(f"   {i}. {status_emoji} {flow.get('MasterLabel')} ({flow.get('ProcessType', 'Unknown')})")
    
    # Step 4: Fetch detailed metadata for each flow
    print()
    print("=" * 80)
    print("  STEP 4: Fetch Detailed Flow Metadata")
    print("=" * 80)
    print()
    
    detailed_flows = []
    for i, flow in enumerate(flows, 1):
        developer_name = flow.get('DeveloperName')
        label = flow.get('MasterLabel')
        print(f"   [{i}/{len(flows)}] Fetching: {label}...", end=" ")
        
        # Fetch active version metadata
        flow_metadata = fetch_active_flow_metadata(auth, developer_name)
        
        if flow_metadata:
            detailed_flows.append({
                'Id': flow_metadata.get('Id'),
                'FullName': developer_name,
                'MasterLabel': label,
                'Metadata': flow_metadata.get('Metadata', {}),
                'ProcessType': flow_metadata.get('ProcessType'),
                'TriggerType': flow_metadata.get('TriggerType'),
                'Status': flow_metadata.get('Status'),
                'ApiVersion': flow_metadata.get('ApiVersion'),
                'VersionNumber': flow_metadata.get('VersionNumber')
            })
            print("✅")
        else:
            # Still include basic info even without detailed metadata
            detailed_flows.append({
                'Id': flow.get('Id'),
                'FullName': developer_name,
                'MasterLabel': label,
                'Metadata': {
                    'processType': flow.get('ProcessType'),
                    'description': flow.get('Description'),
                    'status': flow.get('Status')
                },
                'ProcessType': flow.get('ProcessType'),
                'Status': flow.get('Status'),
                'ApiVersion': flow.get('ApiVersion')
            })
            print("⚠️ (basic only)")
    
    print(f"\n✅ Fetched metadata for {len(detailed_flows)} flows")
    
    # Step 5: Save flows to JSON
    print()
    print("=" * 80)
    print("  STEP 5: Save Flow Metadata")
    print("=" * 80)
    
    # Save to org_flows directory
    output_dir = os.path.join(os.path.dirname(__file__), 'org_flows')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save individual flow files
    for flow in detailed_flows:
        flow_file = os.path.join(output_dir, f"{flow['FullName']}.json")
        with open(flow_file, 'w') as f:
            json.dump(flow, f, indent=2, default=str)
    
    # Save all flows in one file
    all_flows_file = os.path.join(output_dir, '_all_flows.json')
    with open(all_flows_file, 'w') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'instance_url': auth['instance_url'],
            'flow_count': len(detailed_flows),
            'flows': detailed_flows
        }, f, indent=2, default=str)
    
    print(f"✅ Saved {len(detailed_flows)} flows to: {output_dir}/")
    print(f"   • Individual files: {output_dir}/<flow_name>.json")
    print(f"   • Combined file: {output_dir}/_all_flows.json")
    
    # Step 6: Create baseline
    print()
    print("=" * 80)
    print("  STEP 6: Create Baseline from Org Flows")
    print("=" * 80)
    
    storage_path = os.path.join(os.path.dirname(__file__), 'flow_baselines')
    baseline_manager = BaselineManager(storage_path)
    
    # Prepare for baseline
    flows_metadata = []
    analysis_results = []
    
    for flow in detailed_flows:
        metadata = flow.get('Metadata', {})
        
        flows_metadata.append({
            'Id': flow.get('Id'),
            'FullName': flow.get('FullName'),
            'Metadata': metadata
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
        name=f"Org Baseline {datetime.now().strftime('%Y-%m-%d')}",
        description=f"Baseline from {config.salesforce.instance_url}",
        created_by=config.salesforce.username
    )
    
    print(f"✅ Baseline created: {baseline_metadata.id}")
    print(f"   Name: {baseline_metadata.name}")
    print(f"   Version: {baseline_metadata.version}")
    print(f"   Flows: {baseline_metadata.flow_count}")
    
    # Summary
    print()
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"""
✅ Successfully connected to your Salesforce org!

📊 Org Details:
   Instance: {auth['instance_url']}
   Username: {config.salesforce.username}

📦 Flows Retrieved: {len(detailed_flows)}
""")
    
    # List flows by type
    flow_types = {}
    for flow in detailed_flows:
        ptype = flow.get('ProcessType', 'Unknown')
        flow_types[ptype] = flow_types.get(ptype, 0) + 1
    
    print("📋 Flows by Type:")
    for ptype, count in sorted(flow_types.items()):
        print(f"   • {ptype}: {count}")
    
    print(f"""
💾 Files Created:
   • {output_dir}/*.json (individual flow files)
   • {output_dir}/_all_flows.json (combined)
   • flow_baselines/ (baseline data)

🚀 Next Steps:
   1. Run: python run_scenario_tests.py --max 5
   2. Query your flows: model.query("What does <flow_name> do?")
   3. Run regression: python demo_regression.py
""")


if __name__ == "__main__":
    main()

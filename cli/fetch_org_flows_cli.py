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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

# Add parent directory and src to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.baseline_manager import BaselineManager
from src.model import create_model_from_config


def get_oauth_token(
    client_id=None, 
    client_secret=None, 
    instance_url=None, 
    username=None, 
    password=None, 
    security_token=None
):
    """
    Get Salesforce access token using OAuth 2.0 Client Credentials or Password flow.
    
    All parameters are optional - if not provided, they will be read from environment
    variables (.env file):
        - SF_CLIENT_ID
        - SF_CLIENT_SECRET
        - SF_INSTANCE_URL
        - SF_USERNAME
        - SF_PASSWORD
        - SF_SECURITY_TOKEN
    
    Args:
        client_id: Connected App Consumer Key (or SF_CLIENT_ID env var)
        client_secret: Connected App Consumer Secret (or SF_CLIENT_SECRET env var)
        instance_url: Salesforce instance URL (or SF_INSTANCE_URL env var)
        username: Salesforce username for password flow (or SF_USERNAME env var)
        password: Salesforce password for password flow (or SF_PASSWORD env var)
        security_token: Salesforce security token (or SF_SECURITY_TOKEN env var)
    
    Returns:
        dict with access_token, instance_url, and token_type, or None on failure
    
    Usage:
        # Read all credentials from .env file
        auth = get_oauth_token()
        
        # Override specific values
        auth = get_oauth_token(instance_url="https://test.salesforce.com")
        
        # Provide all values manually
        auth = get_oauth_token(
            client_id="your_consumer_key",
            client_secret="your_consumer_secret",
            username="your@email.com",
            password="your_password"
        )
    """
    # Read from environment variables if not provided
    client_id = client_id or os.environ.get('SF_CLIENT_ID')
    client_secret = client_secret or os.environ.get('SF_CLIENT_SECRET')
    instance_url = instance_url or os.environ.get('SF_INSTANCE_URL')
    username = username or os.environ.get('SF_USERNAME')
    password = password or os.environ.get('SF_PASSWORD')
    security_token = security_token or os.environ.get('SF_SECURITY_TOKEN', '')
    
    # Validate required credentials
    if not client_id or not client_secret:
        print("❌ Missing OAuth credentials!")
        print("   Please set SF_CLIENT_ID and SF_CLIENT_SECRET in your .env file")
        print("   Or provide them as function parameters")
        return None
    
    print("🔐 Getting OAuth access token...")
    print(f"   Client ID: {client_id[:10]}...{client_id[-4:]}" if len(client_id) > 14 else f"   Client ID: {client_id}")
    
    # Determine login URL
    if instance_url:
        # Use custom domain or sandbox
        login_url = instance_url.rstrip('/')
        print(f"   Instance URL: {login_url}")
    else:
        login_url = "https://login.salesforce.com"
        print(f"   Login URL: {login_url} (default)")
    
    token_url = f"{login_url}/services/oauth2/token"
    
    try:
        # Determine which flow to use
        if username and password:
            # Password Flow
            print(f"   Using Password Flow for user: {username}")
            data = {
                'grant_type': 'password',
                'client_id': client_id,
                'client_secret': client_secret,
                'username': username,
                'password': password + security_token
            }
        else:
            # Client Credentials Flow (Server-to-Server)
            print("   Using Client Credentials Flow")
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
        
        # Encode the data
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        # Make the request
        req = urllib.request.Request(token_url, data=encoded_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        access_token = result.get('access_token')
        returned_instance_url = result.get('instance_url', instance_url)
        
        if not access_token:
            print("❌ No access token in response")
            return None
        
        print(f"✅ OAuth authentication successful!")
        print(f"   Instance URL: {returned_instance_url}")
        print(f"   Token Type: {result.get('token_type', 'Bearer')}")
        
        return {
            'access_token': access_token,
            'instance_url': returned_instance_url,
            'token_type': result.get('token_type', 'Bearer'),
            'username': username or result.get('username', 'OAuth User'),
            'issued_at': result.get('issued_at'),
            'signature': result.get('signature')
        }
        
    except urllib.error.HTTPError as e:
        print(f"❌ OAuth Error: {e.code}")
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print(f"   Error: {error_body.get('error', 'Unknown')}")
            print(f"   Description: {error_body.get('error_description', 'No description')}")
        except:
            print(f"   Response: {e.read().decode('utf-8')[:200]}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


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


def fetch_all_flows(auth, flow_name=None):
    """Fetch all Flow metadata from Salesforce using Tooling API
    
    Args:
        auth: Authentication dict with access_token and instance_url
        flow_name: Optional - specific flow DeveloperName or MasterLabel to filter (for testing)
    
    Returns:
        List of flow definition records
    """
    print("\n📥 Fetching Flow definitions from Salesforce...")
    
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    
    # Query to get flow definitions (with optional filter for testing)
    if flow_name:
        print(f"   🔍 Filtering for flow: {flow_name}")
        query = f"""
        SELECT Id, DeveloperName, MasterLabel, Description, ActiveVersionId
        FROM FlowDefinition
        WHERE (DeveloperName = '{flow_name}' OR MasterLabel = '{flow_name}')
        AND ActiveVersionId != null
        ORDER BY MasterLabel
        """
    else:
        query = """
        SELECT Id, DeveloperName, MasterLabel, Description, ActiveVersionId
        FROM FlowDefinition
        WHERE ActiveVersionId != null
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


def test_single_flow(flow_name):
    """
    Test fetching a single flow by name.
    Useful for testing if the connection and query are working.
    
    Args:
        flow_name: The DeveloperName or MasterLabel of the flow to test
    
    Usage:
        python fetch_org_flows_cli.py --test "My_Flow_Name"
    """
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     TEST MODE: Fetching Single Flow                         ║
║                        Flow: {flow_name:<43} ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Authenticate
    auth = get_oauth_token()
    if not auth:
        auth = get_sf_cli_auth()
    
    if not auth:
        print("❌ Authentication failed!")
        return False
    
    # Try fetching the specific flow
    print(f"\n🔍 Testing query for flow: {flow_name}")
    print("-" * 60)
    
    flows = fetch_active_flows(auth, flow_name=flow_name)
    
    if not flows:
        print(f"   No active flow found with name '{flow_name}'")
        print("   Trying FlowDefinition query...")
        flows = fetch_all_flows(auth, flow_name=flow_name)
    
    if flows:
        print(f"\n✅ SUCCESS! Found {len(flows)} flow(s):")
        for flow in flows:
            print(f"\n   Flow Details:")
            print(f"   • ID: {flow.get('Id')}")
            print(f"   • DeveloperName: {flow.get('Definition', {}).get('DeveloperName') or flow.get('DeveloperName')}")
            print(f"   • MasterLabel: {flow.get('MasterLabel')}")
            print(f"   • Status: {flow.get('Status', 'N/A')}")
            print(f"   • ProcessType: {flow.get('ProcessType', 'N/A')}")
            print(f"   • Has Metadata: {'Yes' if flow.get('Metadata') else 'No'}")
        return True
    else:
        print(f"\n❌ FAILED: No flow found with name '{flow_name}'")
        print("\n   Possible reasons:")
        print("   • Flow name is incorrect (check spelling)")
        print("   • Flow doesn't exist in the org")
        print("   • Flow is not active")
        print("   • Insufficient permissions")
        return False


def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Fetch Flow metadata from Salesforce')
    parser.add_argument('--test', '-t', metavar='FLOW_NAME', 
                        help='Test mode: fetch a single flow by DeveloperName or MasterLabel')
    parser.add_argument('--flow', '-f', metavar='FLOW_NAME',
                        help='Fetch only a specific flow (for production use)')
    args = parser.parse_args()
    
    # Test mode - fetch single flow
    if args.test:
        success = test_single_flow(args.test)
        sys.exit(0 if success else 1)
    
    # Store flow filter for later use
    flow_filter = args.flow
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         FETCH REAL FLOW METADATA FROM YOUR SALESFORCE ORG                   ║
║                (Using Salesforce CLI or OAuth)                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Get authentication
    print("=" * 80)
    print("  STEP 1: Authenticate to Salesforce")
    print("=" * 80)
    
    auth = None
    
    # Check for OAuth credentials in .env file (loaded automatically)
    client_id = os.environ.get('SF_CLIENT_ID')
    client_secret = os.environ.get('SF_CLIENT_SECRET')
    
    if client_id and client_secret:
        print("🔑 Found OAuth credentials in .env file")
        # All credentials are read from .env inside get_oauth_token()
        auth = get_oauth_token()
    
    # Fallback to SF CLI if OAuth fails or not configured
    if not auth:
        print("\n🔄 Trying Salesforce CLI authentication...")
        auth = get_sf_cli_auth("saurabh@medisale.com")
    
    if not auth:
        print("\n⚠️  Authentication failed. Options:")
        print("\n   Option 1: Add credentials to .env file:")
        print("      SF_CLIENT_ID=your_consumer_key")
        print("      SF_CLIENT_SECRET=your_consumer_secret")
        print("      SF_INSTANCE_URL=https://your-domain.my.salesforce.com")
        print("      SF_USERNAME=your@email.com        # For password flow")
        print("      SF_PASSWORD=your_password         # For password flow")
        print("      SF_SECURITY_TOKEN=your_token      # Optional")
        print("\n   Option 2: Use Salesforce CLI")
        print("      sf org login web -a myorg")
        return
    
    # Step 2: Fetch all active flows
    print()
    print("=" * 80)
    print("  STEP 2: Fetch Active Flows")
    print("=" * 80)
    
    if flow_filter:
        print(f"   📌 Filtering for specific flow: {flow_filter}")
    
    flows = fetch_active_flows(auth, flow_name=flow_filter)
    
    if not flows:
        # Try fetching flow definitions instead
        print("   Trying alternative method...")
        flow_defs = fetch_all_flows(auth, flow_name=flow_filter)
        
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
        if flow_filter:
            print(f"⚠️  No flows found matching '{flow_filter}'")
        else:
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

"""
Salesforce Client for fetching Flow metadata via REST/Tooling API.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SalesforceConnection:
    """Salesforce connection details."""
    instance_url: str
    access_token: str
    api_version: str = "59.0"


class SalesforceClient:
    """
    Client for interacting with Salesforce REST and Tooling APIs.
    Fetches Flow metadata and other components.
    """
    
    def __init__(self, connection: SalesforceConnection):
        """Initialize with connection details."""
        self.connection = connection
        self.base_url = f"{connection.instance_url}/services/data/v{connection.api_version}"
        self.tooling_url = f"{self.base_url}/tooling"
        
    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Salesforce."""
        headers = {
            "Authorization": f"Bearer {self.connection.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        request_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise SalesforceAPIError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise SalesforceAPIError(f"Connection error: {e.reason}")
    
    def query(self, soql: str) -> List[Dict]:
        """Execute SOQL query."""
        encoded_query = urllib.parse.quote(soql)
        url = f"{self.base_url}/query/?q={encoded_query}"
        result = self._make_request(url)
        return result.get('records', [])
    
    def tooling_query(self, soql: str) -> List[Dict]:
        """Execute Tooling API SOQL query."""
        encoded_query = urllib.parse.quote(soql)
        url = f"{self.tooling_url}/query/?q={encoded_query}"
        result = self._make_request(url)
        return result.get('records', [])
    
    def get_flow_definitions(self) -> List[Dict]:
        """Get all Flow definitions (metadata about flows)."""
        soql = """
            SELECT Id, DeveloperName, MasterLabel, Description, 
                   ActiveVersionId, LatestVersionId, ProcessType,
                   LastModifiedDate, LastModifiedById
            FROM FlowDefinition
        """
        return self.tooling_query(soql)
    
    def get_flow_versions(self, flow_definition_id: Optional[str] = None) -> List[Dict]:
        """Get Flow versions (actual flow configurations)."""
        soql = """
            SELECT Id, FlowDefinitionId, VersionNumber, Status,
                   Description, ProcessType, LastModifiedDate
            FROM Flow
        """
        if flow_definition_id:
            soql += f" WHERE FlowDefinitionId = '{flow_definition_id}'"
        
        return self.tooling_query(soql)
    
    def get_flow_metadata(self, flow_id: str) -> Dict:
        """Get full Flow metadata including all elements."""
        url = f"{self.tooling_url}/sobjects/Flow/{flow_id}"
        return self._make_request(url)
    
    def get_all_active_flows_metadata(self) -> List[Dict]:
        """
        Fetch complete metadata for all active flows.
        Returns list of full flow definitions with all elements.
        """
        flows_metadata = []
        
        # Get all flow definitions
        definitions = self.get_flow_definitions()
        
        for definition in definitions:
            active_version_id = definition.get('ActiveVersionId')
            
            if active_version_id:
                try:
                    # Fetch full metadata for active version
                    full_metadata = self.get_flow_metadata(active_version_id)
                    full_metadata['_definition'] = definition
                    full_metadata['_fetched_at'] = datetime.now().isoformat()
                    flows_metadata.append(full_metadata)
                except SalesforceAPIError as e:
                    print(f"Warning: Could not fetch flow {definition.get('DeveloperName')}: {e}")
        
        return flows_metadata
    
    def get_all_flows_metadata(self, include_inactive: bool = False) -> List[Dict]:
        """
        Fetch metadata for all flows (active and optionally inactive).
        """
        flows_metadata = []
        definitions = self.get_flow_definitions()
        
        for definition in definitions:
            # Determine which version to fetch
            if include_inactive:
                version_id = definition.get('LatestVersionId') or definition.get('ActiveVersionId')
            else:
                version_id = definition.get('ActiveVersionId')
            
            if version_id:
                try:
                    full_metadata = self.get_flow_metadata(version_id)
                    full_metadata['_definition'] = definition
                    full_metadata['_fetched_at'] = datetime.now().isoformat()
                    full_metadata['_is_active'] = (version_id == definition.get('ActiveVersionId'))
                    flows_metadata.append(full_metadata)
                except SalesforceAPIError as e:
                    print(f"Warning: Could not fetch flow {definition.get('DeveloperName')}: {e}")
        
        return flows_metadata
    
    def get_flow_by_name(self, developer_name: str) -> Optional[Dict]:
        """Fetch a specific flow by its DeveloperName."""
        soql = f"""
            SELECT Id, DeveloperName, ActiveVersionId, LatestVersionId
            FROM FlowDefinition
            WHERE DeveloperName = '{developer_name}'
        """
        definitions = self.tooling_query(soql)
        
        if not definitions:
            return None
        
        definition = definitions[0]
        version_id = definition.get('ActiveVersionId') or definition.get('LatestVersionId')
        
        if version_id:
            full_metadata = self.get_flow_metadata(version_id)
            full_metadata['_definition'] = definition
            full_metadata['_fetched_at'] = datetime.now().isoformat()
            return full_metadata
        
        return None


class SalesforceAPIError(Exception):
    """Exception for Salesforce API errors."""
    pass


class MockSalesforceClient:
    """
    Mock client for testing without actual Salesforce connection.
    Simulates fetching flows from local files.
    """
    
    def __init__(self, metadata_directory: str):
        """Initialize with directory containing flow JSON files."""
        self.metadata_directory = metadata_directory
        
    def get_all_active_flows_metadata(self) -> List[Dict]:
        """Load all flow JSON files from the directory."""
        import os
        
        flows = []
        
        if not os.path.exists(self.metadata_directory):
            return flows
        
        for filename in os.listdir(self.metadata_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(self.metadata_directory, filename)
                try:
                    with open(filepath, 'r') as f:
                        flow_data = json.load(f)
                        flow_data['_source_file'] = filename
                        flow_data['_fetched_at'] = datetime.now().isoformat()
                        flows.append(flow_data)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load {filename}: {e}")
        
        return flows
    
    def get_all_flows_metadata(self, include_inactive: bool = False) -> List[Dict]:
        """Same as get_all_active_flows_metadata for mock client."""
        return self.get_all_active_flows_metadata()
    
    def get_flow_by_name(self, developer_name: str) -> Optional[Dict]:
        """Find flow by name in local files."""
        import os
        
        # Try exact filename match
        filepath = os.path.join(self.metadata_directory, f"{developer_name}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        
        # Search in all files
        for flow in self.get_all_active_flows_metadata():
            if flow.get('fullName') == developer_name or flow.get('FullName') == developer_name:
                return flow
            # Check Metadata wrapper
            metadata = flow.get('Metadata', {})
            if metadata.get('fullName') == developer_name:
                return flow
        
        return None


def create_salesforce_client(
    instance_url: Optional[str] = None,
    access_token: Optional[str] = None,
    api_version: str = "59.0",
    mock_directory: Optional[str] = None
) -> 'SalesforceClient | MockSalesforceClient':
    """
    Factory function to create appropriate Salesforce client.
    
    If mock_directory is provided, returns MockSalesforceClient.
    Otherwise, returns real SalesforceClient if credentials provided.
    """
    if mock_directory:
        return MockSalesforceClient(mock_directory)
    
    if instance_url and access_token:
        connection = SalesforceConnection(
            instance_url=instance_url,
            access_token=access_token,
            api_version=api_version
        )
        return SalesforceClient(connection)
    
    raise ValueError("Either mock_directory or (instance_url + access_token) must be provided")


# OAuth authentication helper
def authenticate_oauth(
    username: str,
    password: str,
    security_token: str,
    consumer_key: str,
    consumer_secret: str,
    login_url: str = "https://login.salesforce.com"
) -> SalesforceConnection:
    """
    Authenticate with Salesforce using OAuth 2.0 password flow.
    Returns SalesforceConnection with access token.
    """
    token_url = f"{login_url}/services/oauth2/token"
    
    data = {
        "grant_type": "password",
        "client_id": consumer_key,
        "client_secret": consumer_secret,
        "username": username,
        "password": f"{password}{security_token}"
    }
    
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    
    req = urllib.request.Request(token_url, data=encoded_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            return SalesforceConnection(
                instance_url=result['instance_url'],
                access_token=result['access_token']
            )
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise SalesforceAPIError(f"Authentication failed: {error_body}")


if __name__ == "__main__":
    # Demo with mock client
    import os
    
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 60)
    print("Salesforce Client Demo (Mock Mode)")
    print("=" * 60)
    
    # Use mock client with project root as metadata directory
    client = create_salesforce_client(mock_directory=project_root)
    
    flows = client.get_all_active_flows_metadata()
    print(f"\nFound {len(flows)} flow(s):")
    
    for flow in flows:
        name = flow.get('fullName') or flow.get('FullName') or flow.get('_source_file', 'Unknown')
        print(f"  - {name}")

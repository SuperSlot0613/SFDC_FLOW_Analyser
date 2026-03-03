"""
Baseline Manager for storing and managing Flow metadata baselines.
Handles versioning, storage, and retrieval of baseline snapshots.
"""

import json
import os
import hashlib
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class BaselineStatus(Enum):
    """Status of a baseline."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"


@dataclass
class BaselineMetadata:
    """Metadata about a baseline snapshot."""
    id: str
    name: str
    description: str
    created_at: str
    created_by: str
    flow_count: int
    status: str
    version: int
    checksum: str
    tags: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BaselineMetadata':
        return cls(**data)


@dataclass
class FlowBaseline:
    """Baseline data for a single flow."""
    flow_name: str
    flow_id: str
    version_number: int
    checksum: str
    element_count: int
    analysis_summary: Dict
    metadata: Dict
    captured_at: str


class BaselineManager:
    """
    Manages baseline storage for Flow metadata.
    Supports versioning, comparison, and rollback.
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize baseline manager.
        
        Args:
            storage_path: Directory to store baselines
        """
        self.storage_path = storage_path
        self.baselines_dir = os.path.join(storage_path, "baselines")
        self.active_baseline_file = os.path.join(storage_path, "active_baseline.json")
        self.history_file = os.path.join(storage_path, "baseline_history.json")
        
        # Ensure directories exist
        os.makedirs(self.baselines_dir, exist_ok=True)
        
        # Initialize history if doesn't exist
        if not os.path.exists(self.history_file):
            self._save_history([])
    
    def _generate_id(self) -> str:
        """Generate unique baseline ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"baseline_{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data integrity verification."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _calculate_flow_checksum(self, flow_data: Dict) -> str:
        """Calculate checksum for a single flow."""
        # Extract key elements for comparison (ignore timestamps, IDs)
        key_elements = {
            'elements': flow_data.get('Metadata', {}).get('actionCalls', []),
            'decisions': flow_data.get('Metadata', {}).get('decisions', []),
            'assignments': flow_data.get('Metadata', {}).get('assignments', []),
            'recordCreates': flow_data.get('Metadata', {}).get('recordCreates', []),
            'recordUpdates': flow_data.get('Metadata', {}).get('recordUpdates', []),
            'recordLookups': flow_data.get('Metadata', {}).get('recordLookups', []),
            'recordDeletes': flow_data.get('Metadata', {}).get('recordDeletes', []),
            'screens': flow_data.get('Metadata', {}).get('screens', []),
            'subflows': flow_data.get('Metadata', {}).get('subflows', []),
            'loops': flow_data.get('Metadata', {}).get('loops', []),
            'start': flow_data.get('Metadata', {}).get('start', {}),
            'processType': flow_data.get('Metadata', {}).get('processType'),
            'status': flow_data.get('Metadata', {}).get('status'),
        }
        return self._calculate_checksum(key_elements)
    
    def _load_history(self) -> List[Dict]:
        """Load baseline history."""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self, history: List[Dict]):
        """Save baseline history."""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def create_baseline(
        self,
        flows_metadata: List[Dict],
        analysis_results: List[Dict],
        name: str = "auto",
        description: str = "",
        created_by: str = "system",
        tags: Optional[List[str]] = None
    ) -> BaselineMetadata:
        """
        Create a new baseline from flow metadata and analysis results.
        
        Args:
            flows_metadata: List of raw flow metadata from Salesforce
            analysis_results: List of analysis results for each flow
            name: Baseline name (auto-generated if "auto")
            description: Description of this baseline
            created_by: Who created this baseline
            tags: Optional tags for categorization
            
        Returns:
            BaselineMetadata for the created baseline
        """
        baseline_id = self._generate_id()
        timestamp = datetime.now().isoformat()
        
        if name == "auto":
            name = f"Baseline {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Build flow baselines
        flow_baselines = []
        for flow_data, analysis in zip(flows_metadata, analysis_results):
            # Extract flow name
            flow_name = (
                flow_data.get('FullName') or 
                flow_data.get('fullName') or 
                flow_data.get('Metadata', {}).get('fullName') or
                flow_data.get('_source_file', 'unknown')
            )
            
            # Count elements
            metadata = flow_data.get('Metadata', {})
            element_count = sum([
                len(metadata.get('actionCalls', []) or []),
                len(metadata.get('decisions', []) or []),
                len(metadata.get('assignments', []) or []),
                len(metadata.get('recordCreates', []) or []),
                len(metadata.get('recordUpdates', []) or []),
                len(metadata.get('recordLookups', []) or []),
                len(metadata.get('screens', []) or []),
                len(metadata.get('subflows', []) or []),
                len(metadata.get('loops', []) or []),
            ])
            
            flow_baseline = FlowBaseline(
                flow_name=flow_name,
                flow_id=flow_data.get('Id', ''),
                version_number=flow_data.get('VersionNumber', 1),
                checksum=self._calculate_flow_checksum(flow_data),
                element_count=element_count,
                analysis_summary=analysis,
                metadata=flow_data,
                captured_at=timestamp
            )
            flow_baselines.append(asdict(flow_baseline))
        
        # Calculate overall checksum
        overall_checksum = self._calculate_checksum(flow_baselines)
        
        # Get next version number
        history = self._load_history()
        version = len(history) + 1
        
        # Create baseline metadata
        baseline_metadata = BaselineMetadata(
            id=baseline_id,
            name=name,
            description=description,
            created_at=timestamp,
            created_by=created_by,
            flow_count=len(flow_baselines),
            status=BaselineStatus.ACTIVE.value,
            version=version,
            checksum=overall_checksum,
            tags=tags or []
        )
        
        # Save baseline data
        baseline_data = {
            'metadata': baseline_metadata.to_dict(),
            'flows': flow_baselines
        }
        
        baseline_file = os.path.join(self.baselines_dir, f"{baseline_id}.json")
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        # Update history
        history.append(baseline_metadata.to_dict())
        self._save_history(history)
        
        # Set as active baseline
        self.set_active_baseline(baseline_id)
        
        return baseline_metadata
    
    def get_baseline(self, baseline_id: str) -> Optional[Dict]:
        """Get a specific baseline by ID."""
        baseline_file = os.path.join(self.baselines_dir, f"{baseline_id}.json")
        
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_active_baseline(self) -> Optional[Dict]:
        """Get the currently active baseline."""
        if not os.path.exists(self.active_baseline_file):
            return None
        
        with open(self.active_baseline_file, 'r') as f:
            active_info = json.load(f)
        
        return self.get_baseline(active_info.get('baseline_id'))
    
    def set_active_baseline(self, baseline_id: str):
        """Set a baseline as the active baseline."""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} not found")
        
        active_info = {
            'baseline_id': baseline_id,
            'set_at': datetime.now().isoformat()
        }
        
        with open(self.active_baseline_file, 'w') as f:
            json.dump(active_info, f, indent=2)
    
    def get_baseline_history(self) -> List[BaselineMetadata]:
        """Get list of all baselines."""
        history = self._load_history()
        return [BaselineMetadata.from_dict(h) for h in history]
    
    def get_flow_from_baseline(self, baseline_id: str, flow_name: str) -> Optional[Dict]:
        """Get a specific flow from a baseline."""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            return None
        
        for flow in baseline.get('flows', []):
            if flow['flow_name'] == flow_name:
                return flow
        return None
    
    def delete_baseline(self, baseline_id: str, archive: bool = True):
        """
        Delete or archive a baseline.
        
        Args:
            baseline_id: ID of baseline to delete
            archive: If True, move to archive instead of deleting
        """
        baseline_file = os.path.join(self.baselines_dir, f"{baseline_id}.json")
        
        if not os.path.exists(baseline_file):
            raise ValueError(f"Baseline {baseline_id} not found")
        
        if archive:
            archive_dir = os.path.join(self.storage_path, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            shutil.move(baseline_file, os.path.join(archive_dir, f"{baseline_id}.json"))
            
            # Update status in history
            history = self._load_history()
            for item in history:
                if item['id'] == baseline_id:
                    item['status'] = BaselineStatus.ARCHIVED.value
            self._save_history(history)
        else:
            os.remove(baseline_file)
            
            # Remove from history
            history = self._load_history()
            history = [h for h in history if h['id'] != baseline_id]
            self._save_history(history)
    
    def export_baseline(self, baseline_id: str, output_path: str):
        """Export a baseline to a file."""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} not found")
        
        with open(output_path, 'w') as f:
            json.dump(baseline, f, indent=2)
    
    def import_baseline(self, input_path: str) -> BaselineMetadata:
        """Import a baseline from a file."""
        with open(input_path, 'r') as f:
            baseline_data = json.load(f)
        
        # Generate new ID
        old_id = baseline_data['metadata']['id']
        new_id = self._generate_id()
        baseline_data['metadata']['id'] = new_id
        baseline_data['metadata']['imported_from'] = old_id
        baseline_data['metadata']['imported_at'] = datetime.now().isoformat()
        
        # Save
        baseline_file = os.path.join(self.baselines_dir, f"{new_id}.json")
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        # Update history
        history = self._load_history()
        history.append(baseline_data['metadata'])
        self._save_history(history)
        
        return BaselineMetadata.from_dict(baseline_data['metadata'])
    
    def has_active_baseline(self) -> bool:
        """Check if there's an active baseline."""
        return os.path.exists(self.active_baseline_file)
    
    def get_baseline_summary(self, baseline_id: Optional[str] = None) -> Dict:
        """Get summary information about a baseline."""
        if baseline_id:
            baseline = self.get_baseline(baseline_id)
        else:
            baseline = self.get_active_baseline()
        
        if not baseline:
            return {'error': 'No baseline found'}
        
        metadata = baseline.get('metadata', {})
        flows = baseline.get('flows', [])
        
        # Calculate statistics
        total_elements = sum(f.get('element_count', 0) for f in flows)
        
        # Aggregate issues from analysis summaries
        total_issues = 0
        critical_issues = 0
        for flow in flows:
            summary = flow.get('analysis_summary', {})
            issues = summary.get('issues', [])
            total_issues += len(issues)
            critical_issues += sum(1 for i in issues if i.get('severity') == 'critical')
        
        return {
            'id': metadata.get('id'),
            'name': metadata.get('name'),
            'version': metadata.get('version'),
            'created_at': metadata.get('created_at'),
            'flow_count': len(flows),
            'total_elements': total_elements,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'checksum': metadata.get('checksum'),
            'status': metadata.get('status')
        }


if __name__ == "__main__":
    # Demo
    import tempfile
    
    print("=" * 60)
    print("Baseline Manager Demo")
    print("=" * 60)
    
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = BaselineManager(temp_dir)
        
        # Sample flow data
        sample_flows = [{
            'FullName': 'Test_Flow_1',
            'Id': '301xx000000001',
            'VersionNumber': 1,
            'Metadata': {
                'fullName': 'Test_Flow_1',
                'processType': 'AutoLaunchedFlow',
                'status': 'Active',
                'actionCalls': [{'name': 'action1'}],
                'decisions': [{'name': 'decision1'}],
                'assignments': [],
                'recordCreates': [],
                'recordUpdates': [],
                'recordLookups': [],
                'screens': [],
                'subflows': [],
                'loops': [],
                'start': {'locationX': 50, 'locationY': 50}
            }
        }]
        
        sample_analysis = [{
            'flow_name': 'Test_Flow_1',
            'issues': [
                {'severity': 'warning', 'message': 'Missing description'}
            ],
            'metrics': {'element_count': 2}
        }]
        
        # Create baseline
        print("\n1. Creating baseline...")
        baseline_meta = manager.create_baseline(
            flows_metadata=sample_flows,
            analysis_results=sample_analysis,
            name="Initial Baseline",
            description="First baseline for testing",
            created_by="demo_user"
        )
        print(f"   Created: {baseline_meta.id}")
        print(f"   Name: {baseline_meta.name}")
        print(f"   Flows: {baseline_meta.flow_count}")
        
        # Get summary
        print("\n2. Baseline Summary:")
        summary = manager.get_baseline_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # Check active baseline
        print(f"\n3. Has active baseline: {manager.has_active_baseline()}")
        
        # Get history
        print("\n4. Baseline History:")
        for bm in manager.get_baseline_history():
            print(f"   - v{bm.version}: {bm.name} ({bm.created_at})")

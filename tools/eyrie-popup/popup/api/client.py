"""Main API client for Eyrie database."""

import requests
from typing import Optional, Dict, Any

from ..models import ParsedSample, SampleConfig, SampleMetadata
from .upload import UploadHandler
from .format import FormatHandler


class EyrieAPIClient:
    """Client for interacting with Eyrie API."""

    def __init__(self, api_url: str, username: Optional[str] = None, password: Optional[str] = None):
        # Normalize the API URL - if it ends with /api, use it as is, otherwise add /api
        api_url = api_url.rstrip('/')
        if api_url.endswith('/api'):
            self.api_url = api_url
        else:
            self.api_url = f"{api_url}/api"

        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticated = False

        # Initialize handlers
        self.upload_handler = UploadHandler(self)
        self.format_handler = FormatHandler()

    def authenticate(self) -> bool:
        """Authenticate with the Eyrie API."""
        if not self.username or not self.password:
            return True  # No authentication required

        try:
            response = self.session.post(
                f"{self.api_url}/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                }
            )

            if response.status_code == 200:
                auth_data = response.json()
                token = auth_data.get("access_token")
                if token:
                    # Set Authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    self._authenticated = True
                    print("✓ Authenticated with Eyrie API")
                    return True
                else:
                    print("✗ Authentication failed: No token received")
                    return False
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication error: {e}")
            return False

    def upload_sample(self, parsed_sample: ParsedSample, config: SampleConfig, pipeline_datetime_suffix: str = None, force: bool = False) -> bool:
        """Upload a single sample to Eyrie."""
        if not self._authenticated and (self.username and self.password):
            if not self.authenticate():
                return False

        return self.upload_handler.upload_sample(parsed_sample.sample_data, config, pipeline_datetime_suffix, force=force)

    def _convert_to_eyrie_format(self, sample_data, config):
        """Convert sample data to Eyrie database format."""
        return self.format_handler.convert_to_eyrie_format(sample_data, config)

    def test_connection(self) -> bool:
        """Test connection to Eyrie API."""
        try:
            health_url = f"{self.api_url}/system/health"
            print(f"🔍 Testing: {health_url}")
            response = self.session.get(health_url)
            if response.status_code == 200:
                print("✓ Connection to Eyrie API successful")
                return True
            else:
                print(f"✗ Eyrie API health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot connect to Eyrie API: {e}")
            return False

    def upload_sample_metadata(self, sample_id: str, sample_metadata: SampleMetadata, create_missing: bool = False) -> tuple[bool, str]:
        """Upload sample metadata for a single sample.

        Returns:
            tuple: (success: bool, action: str) where action is 'created', 'updated', or 'failed'
        """
        if not self._authenticated and (self.username and self.password):
            if not self.authenticate():
                return False, 'failed'

        try:
            existing_sample = self._get_sample(sample_id)

            sample_metadata_dict = {k: v for k, v in sample_metadata.dict().items() if v is not None}

            if existing_sample:
                api_fields = [
                    'sample_name', 'sample_id', 'sequencing_run_id', 'lims_id',
                    'classification', 'qc', 'comments', 'files',
                    'taxonomic_data', 'flagged_contaminants', 'flagged_top_hits',
                    'nanoplot', 'spike'
                ]

                updated_sample = {k: v for k, v in existing_sample.items() if k in api_fields}
                updated_sample['metadata'] = sample_metadata_dict

                response = self.session.put(
                    f"{self.api_url}/sample/{sample_id}",
                    json=updated_sample
                )

                if response.status_code in [200, 201]:
                    return True, 'updated'
                else:
                    print(f"✗ Failed to update sample {sample_id}: {response.status_code} - {response.text}")
                    return False, 'failed'

            elif create_missing:
                # Create new sample with minimal required fields + sample metadata
                new_sample = {
                    'sample_id': sample_id,
                    'qc': 'unprocessed',
                    'comments': '',
                    'metadata': sample_metadata_dict
                }

                response = self.session.post(
                    f"{self.api_url}/samples",
                    json=new_sample
                )

                if response.status_code in [200, 201]:
                    return True, 'created'
                else:
                    print(f"✗ Failed to create sample {sample_id}: {response.status_code} - {response.text}")
                    return False, 'failed'
            else:
                print(f"✗ Sample {sample_id} not found and create_missing=False")
                return False, 'failed'

        except Exception as e:
            print(f"✗ Error processing sample metadata for {sample_id}: {e}")
            return False, 'failed'

    def _get_sample(self, sample_id: str) -> Optional[dict]:
        """Get existing sample from Eyrie."""
        try:
            response = self.session.get(f"{self.api_url}/sample/{sample_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None


    def create_or_update_seqrun_metadata(self, sequencing_run_id: str, sequencing_metadata: Dict[str, Any]) -> bool:
        """Create or update sequencing run metadata.

        Args:
            sequencing_run_id: The sequencing run identifier
            sequencing_metadata: Parsed sequencing metadata from the markdown report file

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._authenticated and (self.username and self.password):
            if not self.authenticate():
                return False

        try:
            # Check if seqrun already exists
            existing_seqrun = self._get_seqrun(sequencing_run_id)

            if existing_seqrun:
                # Update existing seqrun with sequencing metadata fields
                update_data = {
                    'sequencing_run_id': sequencing_run_id,
                    'pipeline_software': existing_seqrun.get('pipeline_software', 'trana'),
                    'sequencing_metadata': sequencing_metadata
                }

                response = self.session.put(
                    f"{self.api_url}/seqruns/{sequencing_run_id}",
                    json=update_data
                )

                if response.status_code in [200, 201]:
                    print(f"✓ Updated sequencing run {sequencing_run_id} sequencing metadata")
                    return True
                else:
                    print(f"✗ Failed to update seqrun {sequencing_run_id}: {response.status_code} - {response.text}")
                    return False

            else:
                # Create new seqrun with sequencing metadata
                create_data = {
                    'sequencing_run_id': sequencing_run_id,
                    'pipeline_software': 'trana',  # Default pipeline software
                    'sequencing_metadata': sequencing_metadata
                }

                response = self.session.put(
                    f"{self.api_url}/seqruns/{sequencing_run_id}",
                    json=create_data
                )

                if response.status_code in [200, 201]:
                    print(f"✓ Created sequencing run {sequencing_run_id} with sequencing metadata")
                    return True
                else:
                    print(f"✗ Failed to create seqrun {sequencing_run_id}: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"✗ Error processing sequencing run metadata for {sequencing_run_id}: {e}")
            return False

    def _get_seqrun(self, sequencing_run_id: str) -> Optional[dict]:
        """Get existing sequencing run from Eyrie."""
        try:
            response = self.session.get(f"{self.api_url}/seqruns/{sequencing_run_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

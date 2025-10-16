"""Upload handling for Eyrie API."""

from typing import Optional, Dict, Any

from ..models import SampleData, SampleConfig


class UploadHandler:
    """Handles sample upload operations."""

    def __init__(self, client):
        self.client = client

    def upload_sample(self, sample_data: SampleData, config: SampleConfig) -> bool:
        """Upload a single sample to Eyrie."""
        try:
            # Prepare sample data for Eyrie API
            eyrie_sample = self.client.format_handler.convert_to_eyrie_format(sample_data, config)

            # Debug: Print spike field to verify it's being included
            print(f"DEBUG: Uploading spike field: {eyrie_sample.get('spike', 'NOT_FOUND')}")

            # Check if sample already exists
            existing_sample = self._get_sample(sample_data.sample_info.sample_id)

            if existing_sample:
                # Update existing sample
                response = self.client.session.put(
                    f"{self.client.api_url}/samples/{sample_data.sample_info.sample_id}",
                    json=eyrie_sample
                )
                action = "Updated"
            else:
                # Create new sample
                response = self.client.session.post(
                    f"{self.client.api_url}/samples",
                    json=eyrie_sample
                )
                action = "Created"

            if response.status_code in [200, 201]:
                print(f"✓ {action} sample: {sample_data.sample_info.sample_id}")
                return True
            else:
                print(f"✗ Failed to upload sample {sample_data.sample_info.sample_id}: {response.status_code}")
                print(f"  Response: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error uploading sample {sample_data.sample_info.sample_id}: {e}")
            return False

    def _get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get existing sample from Eyrie."""
        try:
            response = self.client.session.get(f"{self.client.api_url}/samples/{sample_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

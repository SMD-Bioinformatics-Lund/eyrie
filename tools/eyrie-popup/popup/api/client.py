"""Main API client for Eyrie database."""

import requests
from typing import Optional

from ..models import ParsedSample, SampleConfig
from .upload import UploadHandler
from .format import FormatHandler


class EyrieAPIClient:
    """Client for interacting with Eyrie API."""

    def __init__(self, api_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
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

    def upload_sample(self, parsed_sample: ParsedSample, config: SampleConfig) -> bool:
        """Upload a single sample to Eyrie."""
        if not self._authenticated and (self.username and self.password):
            if not self.authenticate():
                return False

        return self.upload_handler.upload_sample(parsed_sample.sample_data, config)

    def _convert_to_eyrie_format(self, sample_data, config):
        """Convert sample data to Eyrie database format."""
        return self.format_handler.convert_to_eyrie_format(sample_data, config)

    def test_connection(self) -> bool:
        """Test connection to Eyrie API."""
        try:
            # Health endpoint is at base URL without /api prefix
            base_url = self.api_url.replace('/api', '') if self.api_url.endswith('/api') else self.api_url
            response = self.session.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✓ Connection to Eyrie API successful")
                return True
            else:
                print(f"✗ Eyrie API health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot connect to Eyrie API: {e}")
            return False

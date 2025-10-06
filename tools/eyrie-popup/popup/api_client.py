"""API client for communicating with Eyrie database."""

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from .models import ParsedSample, SampleData, SampleConfig


class EyrieAPIClient:
    """Client for interacting with Eyrie API."""

    def __init__(self, api_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticated = False

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

        return self._upload_sample(parsed_sample.sample_data, config)

    def _upload_sample(self, sample_data: SampleData, config: SampleConfig) -> bool:
        """Upload a single sample to Eyrie."""
        try:
            # Prepare sample data for Eyrie API
            eyrie_sample = self._convert_to_eyrie_format(sample_data, config)

            # Check if sample already exists
            existing_sample = self._get_sample(sample_data.sample_info.sample_id)

            if existing_sample:
                # Update existing sample
                response = self.session.put(
                    f"{self.api_url}/samples/{sample_data.sample_info.sample_id}",
                    json=eyrie_sample
                )
                action = "Updated"
            else:
                # Create new sample
                response = self.session.post(
                    f"{self.api_url}/samples",
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
            response = self.session.get(f"{self.api_url}/samples/{sample_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def _convert_to_eyrie_format(self, sample_data: SampleData, config: SampleConfig) -> Dict[str, Any]:
        """Convert sample data to Eyrie database format."""
        # Determine QC status based on contamination
        qc_status = "unprocessed"
        comments = []

        # Check for contamination
        contaminants = [
            taxa for taxa in sample_data.taxonomic_abundances 
            if taxa.contamination
        ]

        if contaminants:
            contaminant_names = [taxa.species for taxa in contaminants]
            comments.append(f"Potential contamination detected: {', '.join(contaminant_names)}")

        # Prepare statistics
        statistics = {}
        if sample_data.nano_stats_processed:
            stats = sample_data.nano_stats_processed
            statistics = {
                "total_reads": stats.number_of_reads,
                "avg_length": stats.mean_read_length,
                "avg_quality": stats.mean_read_quality,
                "total_bases": stats.total_bases,
                "read_length_n50": stats.read_length_n50
            }
        elif sample_data.nano_stats_unprocessed:
            stats = sample_data.nano_stats_unprocessed
            statistics = {
                "total_reads": stats.number_of_reads,
                "avg_length": stats.mean_read_length,
                "avg_quality": stats.mean_read_quality,
                "total_bases": stats.total_bases,
                "read_length_n50": stats.read_length_n50
            }

        # Prepare taxonomic data as additional metadata
        taxonomic_summary = {
            "total_species": len(sample_data.taxonomic_abundances),
            "contaminants_detected": len(contaminants),
            "hits": [
                {
                    "species": taxa.species,
                    "abundance": round(taxa.abundance * 100, 2),  # Convert to percentage
                    "genus": taxa.genus,
                    "family": taxa.family
                }
                for taxa in sorted(
                    sample_data.taxonomic_abundances, 
                    key=lambda x: x.abundance, 
                    reverse=True
                )
            ]
        }

        # Determine run directory - use config run_directory or fallback to sequencing_run_id
        run_dir = config.run_directory or sample_data.sample_info.sequencing_run_id

        # Structured nanoplot files
        nanoplot_data = None
        if sample_data.nanoplot:
            nanoplot_dict = sample_data.nanoplot.dict()
            # Prepend run_dir to all file paths in the structured nanoplot data
            if nanoplot_dict.get('unprocessed'):
                for field, file_path in nanoplot_dict['unprocessed'].items():
                    if file_path:
                        nanoplot_dict['unprocessed'][field] = f"{run_dir}/{file_path}"
            if nanoplot_dict.get('processed'):
                for field, file_path in nanoplot_dict['processed'].items():
                    if file_path:
                        nanoplot_dict['processed'][field] = f"{run_dir}/{file_path}"
            nanoplot_data = nanoplot_dict

        return {
            "sample_name": sample_data.sample_info.sample_name,
            "sample_id": sample_data.sample_info.sample_id,
            "sequencing_run_id": sample_data.sample_info.sequencing_run_id,
            "lims_id": sample_data.sample_info.lims_id,
            "classification": sample_data.sample_info.classification_type,
            "qc": qc_status,
            "comments": "; ".join(comments) if comments else "",
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
            "krona_file": f"{run_dir}/{sample_data.krona_file}" if sample_data.krona_file else None,
            "quality_plot": f"{run_dir}/{sample_data.fastqc_file}" if sample_data.fastqc_file else None,
            "statistics": statistics,
            "taxonomic_data": taxonomic_summary,
            "nano_stats_processed": sample_data.nano_stats_processed.dict() if sample_data.nano_stats_processed else None,
            "nano_stats_unprocessed": sample_data.nano_stats_unprocessed.dict() if sample_data.nano_stats_unprocessed else None,
            "nanoplot": nanoplot_data
        }

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

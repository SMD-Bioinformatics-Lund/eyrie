"""Upload handling for Eyrie API."""

from typing import Optional, Dict, Any

from ..models import SampleResults, SampleConfig, SampleInfo

class UploadHandler:
    """Handles sample upload operations."""

    def __init__(self, client):
        self.client = client

    def upload_sample(self, sample_data: SampleResults, config: SampleConfig, pipeline_datetime_suffix: str = None) -> bool:
        """Upload a single sample to Eyrie."""
        try:
            # Prepare sample data for Eyrie API
            eyrie_sample = self.client.format_handler.convert_to_eyrie_format(sample_data, config)

            # Handle seqrun upload logic
            should_upload_seqrun = pipeline_datetime_suffix is not None
            if should_upload_seqrun:
                # Check if seqrun already exists (only if not forcing pipeline upload)
                if not pipeline_datetime_suffix:
                    seqrun_exists = self._check_seqrun_exists(sample_data.sample_info.sequencing_run_id)
                    should_upload_seqrun = not seqrun_exists

                if should_upload_seqrun:
                    # Prepare sequencing run data for seqruns collection
                    seqrun_data = self.client.format_handler.extract_seqrun_data(sample_data, config, pipeline_datetime_suffix)

                    # Upload/update sequencing run data first
                    seqrun_success = self._upload_seqrun(seqrun_data)
                    if seqrun_success:
                        print(f"✓ Seqrun data uploaded for {seqrun_data['sequencing_run_id']}")
                    else:
                        print(f"⚠ Warning: Failed to upload/update sequencing run data for {seqrun_data['sequencing_run_id']}")
                else:
                    print(f"ℹ️ Sequencing run {sample_data.sample_info.sequencing_run_id} already exists, skipping seqrun upload")
            else:
                print(f"ℹ️ Skipping sequencing run upload (no sequencing run id or pipeline suffix specified)")

            # Check if sample already exists
            existing_sample = self._get_sample(sample_data.sample_info.sample_id)

            if existing_sample:
                # Update existing sample
                response = self.client.session.put(
                    f"{self.client.api_url}/sample/{sample_data.sample_info.sample_id}",
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

    def _upload_seqrun(self, seqrun_data: Dict[str, Any]) -> bool:
        """Upload/update sequencing run data, preserving existing sequencing_metadata."""
        try:
            sequencing_run_id = seqrun_data['sequencing_run_id']

            # Check if seqrun already exists and get existing data
            try:
                existing_response = self.client.session.get(f"{self.client.api_url}/seqruns/{sequencing_run_id}")
                if existing_response.status_code == 200:
                    existing_data = existing_response.json()

                    # Preserve existing sequencing_metadata if new data doesn't have it
                    if 'sequencing_metadata' not in seqrun_data and existing_data.get('sequencing_metadata'):
                        seqrun_data['sequencing_metadata'] = existing_data['sequencing_metadata']
                        print(f"ℹ️ Preserving existing sequencing_metadata for {sequencing_run_id}")
                    elif 'sequencing_metadata' in seqrun_data:
                        print(f"ℹ️ Updating sequencing_metadata for {sequencing_run_id}")

            except Exception as e:
                print(f"ℹ️ Could not check existing seqrun data (may be new): {e}")

            # Use PUT for upsert operation (create if doesn't exist, update if exists)
            response = self.client.session.put(
                f"{self.client.api_url}/seqruns/{sequencing_run_id}",
                json=seqrun_data
            )

            if response.status_code in [200, 201]:
                return True
            else:
                print(f"  Seqrun response: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"  Seqrun error: {e}")
            return False

    def _check_seqrun_exists(self, sequencing_run_id: str) -> bool:
        """Check if sequencing run already exists."""
        try:
            response = self.client.session.get(f"{self.client.api_url}/seqruns/{sequencing_run_id}")
            return response.status_code == 200
        except:
            return False

    def _get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get existing sample from Eyrie."""
        try:
            response = self.client.session.get(f"{self.client.api_url}/sample/{sample_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def upload_pipeline_files_only(self, sequencing_run_id: str, pipeline_software: str, pipeline_datetime_suffix: str, analysis_output_dirpath: str) -> bool:
        """Upload only pipeline files for a sequencing run."""
        try:
            # Create minimal sample data for pipeline discovery
            sample_info = SampleInfo(
                sample_id="dummy",
                sample_name="dummy", 
                sequencing_run_id=sequencing_run_id,
                lims_id="dummy",
                classification_type="16S",
                pipeline_software=pipeline_software
            )

            sample_results = SampleResults(
                sample_info=sample_info,
                taxonomic_abundances=[],
                nanoplot=None,
                nano_stats_processed=None,
                nano_stats_unprocessed=None,
                krona_file=None,
                fastqc_file=None,
                metadata=None
            )

            config = SampleConfig(
                sample=sample_info,
                analysis_output_dirpath=analysis_output_dirpath
            )

            # Extract seqrun data with pipeline files
            seqrun_data = self.client.format_handler.extract_seqrun_data(sample_results, config, pipeline_datetime_suffix)

            # Upload seqrun data
            success = self._upload_seqrun(seqrun_data)
            if success:
                print(f"✓ Updated pipeline files for sequencing run: {sequencing_run_id}")
            else:
                print(f"✗ Failed to update pipeline files for sequencing run: {sequencing_run_id}")

            return success

        except Exception as e:
            print(f"✗ Error uploading pipeline files for {sequencing_run_id}: {e}")
            return False

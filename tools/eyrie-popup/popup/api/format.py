"""Data formatting for Eyrie API."""

import os
import glob
import re
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from ..models import SampleResults, SampleConfig
from ..parser.pipeline_params import PipelineParamsParser
from ..parser.execution_trace import ExecutionTraceParser
from ..parser.software_versions import SoftwareVersionsParser


class FormatHandler:
    """Handles data format conversion for Eyrie API."""

    def convert_to_eyrie_format(self, sample_data: SampleResults, config: SampleConfig) -> Dict[str, Any]:
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


        # Prepare taxonomic data for database storage
        taxonomic_summary = {
            "total_species": len(sample_data.taxonomic_abundances),
            "contaminants_detected": len(contaminants),
            "hits": [
                {
                    "species": taxa.species,
                    "abundance": round(taxa.abundance * 100, 2),  # Convert to percentage
                    "genus": taxa.genus,
                    "family": taxa.family,
                    "estimated_counts": taxa.estimated_counts
                }
                for taxa in sorted(
                    sample_data.taxonomic_abundances, 
                    key=lambda x: x.abundance, 
                    reverse=True
                )
            ]
        }

        # Structured nanoplot data with nested nanostats
        nanoplot_data = None
        if sample_data.nanoplot:
            nanoplot_dict = sample_data.nanoplot.dict()
            # Add nanostats to nanoplot structure
            if sample_data.nano_stats_unprocessed and nanoplot_dict.get('unprocessed'):
                # Convert existing files to nested structure
                files_dict = nanoplot_dict['unprocessed'].copy()
                nanoplot_dict['unprocessed'] = {
                    "files": files_dict,
                    "nanostats": sample_data.nano_stats_unprocessed.dict()
                }
            elif nanoplot_dict.get('unprocessed'):
                # Convert existing files to nested structure 
                files_dict = nanoplot_dict['unprocessed'].copy()
                nanoplot_dict['unprocessed'] = {
                    "files": files_dict,
                    "nanostats": None
                }

            if sample_data.nano_stats_processed and nanoplot_dict.get('processed'):
                # Convert existing files to nested structure
                files_dict = nanoplot_dict['processed'].copy()
                nanoplot_dict['processed'] = {
                    "files": files_dict,
                    "nanostats": sample_data.nano_stats_processed.dict()
                }
            elif nanoplot_dict.get('processed'):
                # Convert existing files to nested structure
                files_dict = nanoplot_dict['processed'].copy()
                nanoplot_dict['processed'] = {
                    "files": files_dict,
                    "nanostats": None
                }

            nanoplot_data = nanoplot_dict

        # Prepare structured comments
        comments_data = {
            "qc": [],  # Will be populated by QC workflow in web interface
            "other": ""  # User-editable field
        }

        # Add contamination comments to QC comments with timestamp if any
        if comments:
            for comment in comments:
                comments_data["qc"].append({
                    "timestamp": datetime.now().isoformat(),
                    "user": "system",  # System-generated contamination comment
                    "comment": comment
                })

        # Prepare files structure
        files_data = {}
        if sample_data.krona_file:
            files_data["krona"] = sample_data.krona_file
        if sample_data.fastqc_file:
            files_data["fastqc"] = sample_data.fastqc_file

        # Prepare base sample data with new structure
        eyrie_data = {
            "sample_name": sample_data.sample_info.sample_name,
            "sample_id": sample_data.sample_info.sample_id,
            "sequencing_run_id": sample_data.sample_info.sequencing_run_id,
            "lims_id": sample_data.sample_info.lims_id,
            "classification": sample_data.sample_info.classification_type,
            "qc": qc_status,
            "comments": comments_data,
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
            "files": files_data,
            "taxonomic_data": taxonomic_summary,
            "nanoplot": nanoplot_data,
            "spike": sample_data.spike if hasattr(sample_data, 'spike') else None
        }

        # Add sample metadata fields if present
        if sample_data.metadata:
            sample_metadata_dict = {k: v for k, v in sample_data.metadata.dict().items() if v is not None}
            eyrie_data.update(sample_metadata_dict)

        return eyrie_data

    def extract_seqrun_data(self, sample_data: SampleResults, config: SampleConfig, pipeline_datetime_suffix: str = None) -> Dict[str, Any]:
        """Extract sequencing run data for seqruns collection with parsed pipeline data."""

        # Determine pipeline software from config
        pipeline_software = getattr(config, 'pipeline_software', 'trana')  # Default to trana

        seqrun_data = {
            "sequencing_run_id": sample_data.sample_info.sequencing_run_id,
            "pipeline_software": pipeline_software,
            "created_date": datetime.now().isoformat()
        }

        # Discover and parse pipeline files
        pipeline_files, parsed_data = self._discover_and_parse_pipeline_files(
            config.analysis_output_dirpath, pipeline_datetime_suffix
        )

        if pipeline_files:
            seqrun_data["pipeline_files"] = pipeline_files

        # Add parsed structured data
        if parsed_data.get("pipeline_parameters"):
            seqrun_data["pipeline_parameters"] = parsed_data["pipeline_parameters"]
        if parsed_data.get("execution_trace"):
            seqrun_data["execution_trace"] = parsed_data["execution_trace"]
        if parsed_data.get("software_versions"):
            seqrun_data["software_versions"] = parsed_data["software_versions"]

        return seqrun_data

    def _discover_and_parse_pipeline_files(self, analysis_output_dirpath: str, target_suffix: str = None) -> tuple[Dict[str, str], Dict[str, Any]]:
        """Discover and parse pipeline files, returning both file paths and parsed data."""

        pipeline_info_path = f"{analysis_output_dirpath}/pipeline_info"

        if not os.path.exists(pipeline_info_path):
            print(f"⚠ Warning: Pipeline info path does not exist: {pipeline_info_path}")
            return {}, {}

        # Get file paths using existing logic
        pipeline_files = self._discover_pipeline_files(analysis_output_dirpath, target_suffix)

        # Parse structured data from the discovered files
        parsed_data = {}

        try:
            # Parse parameters JSON
            if "params" in pipeline_files:
                params_path = Path(pipeline_info_path) / pipeline_files["params"].replace("pipeline_info/", "")
                if params_path.exists():
                    params_parser = PipelineParamsParser()
                    parsed_params = params_parser.parse(params_path)
                    if parsed_params and params_parser.validate_parsed_data(parsed_params):
                        parsed_data["pipeline_parameters"] = parsed_params
                        print(f"✓ Parsed pipeline parameters: {parsed_params['total_parameters']} parameters")
                    else:
                        print(f"⚠ Warning: Failed to parse pipeline parameters from {params_path}")

            # Parse execution trace TSV
            if "execution_trace" in pipeline_files:
                trace_path = Path(pipeline_info_path) / pipeline_files["execution_trace"].replace("pipeline_info/", "")
                if trace_path.exists():
                    trace_parser = ExecutionTraceParser()
                    parsed_trace = trace_parser.parse(trace_path)
                    if parsed_trace and trace_parser.validate_parsed_data(parsed_trace):
                        parsed_data["execution_trace"] = parsed_trace
                        print(f"✓ Parsed execution trace: {parsed_trace['summary']['total_tasks']} tasks")
                    else:
                        print(f"⚠ Warning: Failed to parse execution trace from {trace_path}")

            # Parse software versions YAML
            if "software_versions" in pipeline_files:
                versions_path = Path(pipeline_info_path) / pipeline_files["software_versions"].replace("pipeline_info/", "")
                if versions_path.exists():
                    versions_parser = SoftwareVersionsParser()
                    parsed_versions = versions_parser.parse(versions_path)
                    if parsed_versions and versions_parser.validate_parsed_data(parsed_versions):
                        parsed_data["software_versions"] = parsed_versions
                        print(f"✓ Parsed software versions: {parsed_versions['summary']['total_tools']} tools")
                    else:
                        print(f"⚠ Warning: Failed to parse software versions from {versions_path}")

        except Exception as e:
            print(f"⚠ Warning: Error parsing pipeline files: {e}")

        # Remove parsed files from pipeline_files (only keep HTML files for viewing)
        html_only_files = {
            k: v for k, v in pipeline_files.items() 
            if k in ["execution_report", "execution_timeline", "pipeline_dag"]
        }

        return html_only_files, parsed_data

    def _discover_pipeline_files(self, analysis_output_dirpath: str, target_suffix: str = None) -> Dict[str, str]:
        """Discover pipeline files in the pipeline_info directory."""

        pipeline_info_path = f"{analysis_output_dirpath}/pipeline_info"

        if not os.path.exists(pipeline_info_path):
            print(f"⚠ Warning: Pipeline info path does not exist: {pipeline_info_path}")
            return {}

        def parse_datetime_from_filename(filename: str) -> datetime:
            """Extract datetime from filename with format YYYY-MM-DD_HH-MM-SS"""
            match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
            if match:
                datetime_str = match.group(1)
                return datetime.strptime(datetime_str, '%Y-%m-%d_%H-%M-%S')
            return datetime.min

        def get_latest_or_target_file(pattern: str) -> str:
            """Get the latest file or file with target suffix matching the pattern"""
            files = glob.glob(os.path.join(pipeline_info_path, pattern))
            if not files:
                return None

            if target_suffix:
                # Look for file with specific suffix
                target_files = [f for f in files if target_suffix in os.path.basename(f)]
                if target_files:
                    return os.path.basename(target_files[0])
                else:
                    # Fallback: find the closest timestamp
                    print(f"⚠ Warning: No exact match for suffix '{target_suffix}' in pattern '{pattern}', using closest timestamp")
                    try:
                        target_dt = datetime.strptime(target_suffix, '%Y-%m-%d_%H-%M-%S')

                        # Find file with closest timestamp
                        closest_file = None
                        min_diff = None

                        for file_path in files:
                            file_dt = parse_datetime_from_filename(os.path.basename(file_path))
                            if file_dt != datetime.min:
                                diff = abs((file_dt - target_dt).total_seconds())
                                if min_diff is None or diff < min_diff:
                                    min_diff = diff
                                    closest_file = file_path

                        if closest_file:
                            closest_name = os.path.basename(closest_file)
                            print(f"   → Using closest match: {closest_name}")
                            return closest_name
                        else:
                            print(f"   → No valid timestamp files found for pattern '{pattern}'")
                            return None
                    except ValueError:
                        print(f"   → Invalid suffix format, falling back to latest file")
                        files.sort(key=parse_datetime_from_filename, reverse=True)
                        return os.path.basename(files[0]) if files else None
            else:
                # Get latest file by datetime
                files.sort(key=parse_datetime_from_filename, reverse=True)
                return os.path.basename(files[0])

        pipeline_files = {}

        # Define file patterns and their keys
        file_patterns = {
            "execution_report": "execution_report_*.html",
            "execution_timeline": "execution_timeline_*.html", 
            "execution_trace": "execution_trace_*.txt",
            "params": "params_*.json",
            "pipeline_dag": "pipeline_dag_*.html"
        }

        for key, pattern in file_patterns.items():
            filename = get_latest_or_target_file(pattern)
            if filename:
                pipeline_files[key] = f"pipeline_info/{filename}"

        versions_file = os.path.join(pipeline_info_path, "software_versions.yml")
        if os.path.exists(versions_file):
            pipeline_files["software_versions"] = "pipeline_info/software_versions.yml"

        return pipeline_files

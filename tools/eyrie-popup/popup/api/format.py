"""Data formatting for Eyrie API."""

import re
from typing import Dict, Any
from datetime import datetime

from ..models import SampleResults, SampleConfig


class FormatHandler:
    """Handles data format conversion for Eyrie API."""

    def extract_sequencing_run_date(self, sequencing_run_id: str):
        """Extract sequence run date from sequencing_run_id and convert to datetime object.

        Splits sequencing_run_id on first '_' and extracts date from the first part.
        Handles both YYYYMMDD and YYMMDD formats and returns datetime object for MongoDB ISODate storage.
        """
        if not sequencing_run_id:
            return None

        first_part = sequencing_run_id.split('_')[0]

        if first_part.isdigit():
            try:
                if len(first_part) == 8:
                    year = int(first_part[:4])
                    month = int(first_part[4:6])
                    day = int(first_part[6:8])
                elif len(first_part) == 6:
                    year = int(f"20{first_part[:2]}")
                    month = int(first_part[2:4])
                    day = int(first_part[4:6])
                else:
                    return None

                # Return datetime object for MongoDB ISODate storage
                return datetime(year, month, day)
            except (ValueError, TypeError):
                # Invalid date values (e.g., month > 12, day > 31)
                return None

        return None

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


        # Prepare taxonomic data as additional metadata
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

        # Use run directory only if provided, no fallback to sequencing_run_id
        run_dir = config.run_directory

        # Structured nanoplot data with nested nanostats
        nanoplot_data = None
        if sample_data.nanoplot:
            nanoplot_dict = sample_data.nanoplot.dict()
            # Prepend run_dir to all file paths only if run_dir is provided
            if nanoplot_dict.get('unprocessed'):
                for field, file_path in nanoplot_dict['unprocessed'].items():
                    if file_path:
                        if run_dir:
                            nanoplot_dict['unprocessed'][field] = f"{run_dir}/{file_path}"
                        else:
                            nanoplot_dict['unprocessed'][field] = file_path
            if nanoplot_dict.get('processed'):
                for field, file_path in nanoplot_dict['processed'].items():
                    if file_path:
                        if run_dir:
                            nanoplot_dict['processed'][field] = f"{run_dir}/{file_path}"
                        else:
                            nanoplot_dict['processed'][field] = file_path

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
            files_data["krona"] = f"{run_dir}/{sample_data.krona_file}" if run_dir else sample_data.krona_file
        if sample_data.fastqc_file:
            files_data["fastqc"] = f"{run_dir}/{sample_data.fastqc_file}" if run_dir else sample_data.fastqc_file

        # Extract sequence run date from sequencing_run_id or use provided value
        sequencing_run_date = sample_data.sample_info.sequencing_run_date
        if sequencing_run_date:
            # If provided in config, parse it to datetime object
            if isinstance(sequencing_run_date, str):
                try:
                    # Handle ISO date format (YYYY-MM-DD)
                    sequencing_run_date = datetime.fromisoformat(sequencing_run_date)
                except ValueError:
                    # Invalid date format, fall back to extraction
                    sequencing_run_date = self.extract_sequencing_run_date(sample_data.sample_info.sequencing_run_id)
        else:
            # Extract from sequencing_run_id
            sequencing_run_date = self.extract_sequencing_run_date(sample_data.sample_info.sequencing_run_id)

        # Prepare base sample data with new structure
        eyrie_data = {
            "sample_name": sample_data.sample_info.sample_name,
            "sample_id": sample_data.sample_info.sample_id,
            "sequencing_run_id": sample_data.sample_info.sequencing_run_id,
            "sequencing_run_date": sequencing_run_date.isoformat() if sequencing_run_date else None,
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

        # Add metadata fields if present
        if sample_data.metadata:
            metadata_dict = {k: v for k, v in sample_data.metadata.dict().items() if v is not None}
            eyrie_data.update(metadata_dict)

        return eyrie_data

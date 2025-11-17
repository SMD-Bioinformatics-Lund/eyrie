"""Data formatting for Eyrie API."""

from typing import Dict, Any
from datetime import datetime

from ..models import SampleResults, SampleConfig


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

        # Prepare sequencing statistics (prefer processed over unprocessed)
        sequencing_statistics = {}
        if sample_data.nano_stats_processed:
            stats = sample_data.nano_stats_processed
            sequencing_statistics = {
                "total_reads": stats.number_of_reads,
                "avg_length": stats.mean_read_length,
                "avg_quality": stats.mean_read_quality,
                "total_bases": stats.total_bases,
                "read_length_n50": stats.read_length_n50
            }
        elif sample_data.nano_stats_unprocessed:
            stats = sample_data.nano_stats_unprocessed
            sequencing_statistics = {
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
            "sequencing_statistics": sequencing_statistics,
            "taxonomic_data": taxonomic_summary,
            "nanoplot": nanoplot_data,
            "spike": sample_data.spike if hasattr(sample_data, 'spike') else None
        }

        # Add metadata fields if present
        if sample_data.metadata:
            metadata_dict = {k: v for k, v in sample_data.metadata.dict().items() if v is not None}
            eyrie_data.update(metadata_dict)

        return eyrie_data

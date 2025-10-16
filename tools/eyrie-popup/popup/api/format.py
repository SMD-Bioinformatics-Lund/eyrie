"""Data formatting for Eyrie API."""

from typing import Dict, Any
from datetime import datetime

from ..models import SampleData, SampleConfig


class FormatHandler:
    """Handles data format conversion for Eyrie API."""

    def convert_to_eyrie_format(self, sample_data: SampleData, config: SampleConfig) -> Dict[str, Any]:
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
            "nanoplot": nanoplot_data,
            "spike": sample_data.spike if hasattr(sample_data, 'spike') else None
        }

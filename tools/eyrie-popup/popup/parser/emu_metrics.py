"""Per-taxon metrics and summary statistics from EMU outputs, using emuse."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from emuse.alignment import read_alignment_metrics
from emuse.qc import summary_stats
from emuse.read_assignment import read_assignment_stats

from ..models import TaxonomicAbundance


def existing_file(directory: Path, filename: Optional[str]) -> Optional[Path]:
    if not filename:
        return None
    path = directory / filename
    return path if path.is_file() else None


def add_taxon_metrics(abundances: List[TaxonomicAbundance], metrics_df, columns: List[str]) -> None:
    metrics = metrics_df.set_index('tax_id')[columns].to_dict(orient='index')
    for taxa in abundances:
        for column, value in metrics.get(taxa.tax_id, {}).items():
            setattr(taxa, column, None if pd.isna(value) else value)


def parse_emu_metrics(abundances: List[TaxonomicAbundance], results_dir: Path, results_config) -> None:
    read_assignment = existing_file(results_dir, results_config.read_assignment_file)
    if read_assignment:
        add_taxon_metrics(abundances, read_assignment_stats(read_assignment), ['median_probability', 'mean_probability'])

    alignment_metrics = existing_file(results_dir, results_config.alignment_metrics_file)
    if alignment_metrics:
        add_taxon_metrics(abundances, read_alignment_metrics(alignment_metrics), ['median_identity', 'median_coverage'])


def parse_classification_qc(multiqc_data: Optional[Path], emu_log: Optional[Path], sample_id: str) -> Optional[Dict[str, Any]]:
    if not multiqc_data:
        return None
    return summary_stats(multiqc_data, sample_id, emu_log).to_dict()

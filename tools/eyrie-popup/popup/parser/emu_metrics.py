"""Per-taxon metrics and summary statistics from EMU outputs, using emuse."""

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pysam
from emuse.alignment import get_align_stats
from emuse.qc import summary_stats
from emuse.read_assignment import read_assignment_summary

from ..models import TaxonomicAbundance

READ_ASSIGNMENT_COLUMNS = {
    'tax id': 'tax_id',
    'median probability*': 'median_probability',
    'mean probability*': 'mean_probability',
}


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


def read_assignment_stats(path: Path) -> pd.DataFrame:
    return read_assignment_summary(path).rename(columns=READ_ASSIGNMENT_COLUMNS)


def alignment_metrics(path: Path) -> pd.DataFrame:
    identities = defaultdict(list)
    coverages = defaultdict(list)
    with pysam.AlignmentFile(str(path)) as alignments:
        for alignment in alignments:
            if alignment.is_unmapped or alignment.is_secondary or alignment.is_supplementary:
                continue
            tax_id = alignment.reference_name.split(':')[0]
            identity, coverage = get_align_stats(alignment, alignments)
            identities[tax_id].append(identity)
            coverages[tax_id].append(coverage)

    rows = [
        {
            'tax_id': tax_id,
            'median_identity': statistics.median(identities[tax_id]),
            'median_coverage': statistics.median(coverages[tax_id]),
        }
        for tax_id in identities
    ]
    return pd.DataFrame(rows, columns=['tax_id', 'median_identity', 'median_coverage'])


def parse_emu_metrics(abundances: List[TaxonomicAbundance], results_dir: Path, results_config) -> None:
    read_assignment = existing_file(results_dir, results_config.read_assignment_file)
    if read_assignment:
        add_taxon_metrics(abundances, read_assignment_stats(read_assignment), ['median_probability', 'mean_probability'])

    alignment = existing_file(results_dir, results_config.alignment_file)
    if alignment:
        add_taxon_metrics(abundances, alignment_metrics(alignment), ['median_identity', 'median_coverage'])


def parse_classification_qc(multiqc_data: Optional[Path], sample_id: str) -> Optional[Dict[str, Any]]:
    if not multiqc_data:
        return None
    return summary_stats(multiqc_data, sample_id)

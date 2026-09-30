"""Taxonomic abundance parsing functionality."""

import glob
from pathlib import Path
from typing import List

from emuse.abundance import read_rel_abundance, to_records

from ..models import TaxonomicAbundance


class TaxonomicParser:
    """Parser for taxonomic abundance data."""

    def __init__(self, seqrun_path: Path):
        self.seqrun_path = seqrun_path

    def parse_rel_abundance(self, results_config) -> List[TaxonomicAbundance]:
        """Parse relative abundance TSV file."""
        if not results_config:
            return []

        pattern = str(self.seqrun_path / results_config.directory / results_config.rel_abundance_file)
        matching_files = glob.glob(pattern)

        if not matching_files:
            return []

        abundances = []
        for row in to_records(read_rel_abundance(matching_files[0])):
            species = row.get('species')
            if not species:
                continue

            abundances.append(TaxonomicAbundance(
                tax_id=row['tax_id'],
                abundance=row['abundance'],
                species=species,
                genus=row.get('genus') or '',
                family=row.get('family') or '',
                order=row.get('order') or '',
                **{'class': row.get('class') or ''},
                phylum=row.get('phylum') or '',
                superkingdom=row.get('superkingdom') or '',
                estimated_counts=row.get('estimated_counts') or 0,
                contamination=str(row.get('contamination', '')).lower() in ['true', '1', 'yes', 'contamination']
            ))

        return abundances

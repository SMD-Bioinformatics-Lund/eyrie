"""Taxonomic abundance parsing functionality."""

import csv
from pathlib import Path
from typing import List

from ..models import TaxonomicAbundance


class TaxonomicParser:
    """Parser for taxonomic abundance data."""

    def __init__(self, seqrun_path: Path):
        self.seqrun_path = seqrun_path

    def parse_rel_abundance(self, results_config) -> List[TaxonomicAbundance]:
        """Parse relative abundance TSV file."""
        if not results_config:
            return []

        abundance_file = self.seqrun_path / results_config.directory / results_config.rel_abundance_file

        if not abundance_file.exists():
            return []

        abundances = []

        try:
            with open(abundance_file, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    # Skip unmapped and unclassified entries
                    species = row.get('species', '')
                    if not species or species in ['unmapped', 'mapped_unclassified']:
                        continue

                    # Check if there's a contamination column in the TSV
                    contamination = False
                    if 'contamination' in row:
                        contamination = row['contamination'].lower() in ['true', '1', 'yes', 'contamination']

                    abundance_data = TaxonomicAbundance(
                        tax_id=row.get('tax_id', ''),
                        abundance=float(row.get('abundance', 0)),
                        species=species,
                        genus=row.get('genus', ''),
                        family=row.get('family', ''),
                        order=row.get('order', ''),
                        **{'class': row.get('class', '')},  # Using dict unpacking for 'class'
                        phylum=row.get('phylum', ''),
                        superkingdom=row.get('superkingdom', ''),
                        estimated_counts=float(row.get('estimated counts', 0)),
                        contamination=contamination
                    )
                    abundances.append(abundance_data)

        except Exception as e:
            print(f"Error parsing abundance file {abundance_file}: {e}")

        return abundances

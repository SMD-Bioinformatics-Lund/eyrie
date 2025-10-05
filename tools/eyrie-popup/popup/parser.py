"""Parser module for extracting data from analysis files."""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional

from .models import (
    SampleConfig,
    SampleData,
    NanoStats,
    TaxonomicAbundance,
    ParsedSample
)


class SampleParser:
    """Parser for single sample sequencing analysis outputs."""

    def __init__(self, config: SampleConfig):
        self.config = config
        self.base_path = Path(config.base_path)
        # Create sequencing run path by combining base_path and run_directory
        run_dir = config.run_directory or config.sample.sequencing_run_id
        self.seqrun_path = self.base_path / run_dir

    def parse_sample(self) -> ParsedSample:
        """Parse the sample analysis data."""
        sample_data = self._parse_sample_data()

        return ParsedSample(sample_data=sample_data)

    def _parse_sample_data(self) -> SampleData:
        """Parse data for the sample."""
        sample_data = SampleData(sample_info=self.config.sample)

        # Parse FastQC
        if self.config.fastqc and self.config.fastqc.enabled:
            sample_data.fastqc_file = self._find_file(
                self.config.fastqc.directory,
                self.config.fastqc.file
            )

        # Parse Krona
        if self.config.krona and self.config.krona.enabled:
            sample_data.krona_file = self._find_file(
                self.config.krona.directory,
                self.config.krona.file
            )

        # Parse MultiQC (shared across samples)
        if self.config.multiqc and self.config.multiqc.enabled:
            sample_data.multiqc_file = self._find_file(
                self.config.multiqc.directory,
                self.config.multiqc.report_file
            )

        # Parse NanoPlot data
        if self.config.nanoplot:
            if self.config.nanoplot.unprocessed and self.config.nanoplot.unprocessed.enabled:
                sample_data.nanoplot_unprocessed = self._parse_nanoplot_stage(
                    self.config.nanoplot.unprocessed
                )
                sample_data.nano_stats_unprocessed = self._parse_nano_stats(
                    self.config.nanoplot.unprocessed.directory,
                    self.config.nanoplot.unprocessed.stats_file
                )

            if self.config.nanoplot.processed and self.config.nanoplot.processed.enabled:
                sample_data.nanoplot_processed = self._parse_nanoplot_stage(
                    self.config.nanoplot.processed
                )
                sample_data.nano_stats_processed = self._parse_nano_stats(
                    self.config.nanoplot.processed.directory,
                    self.config.nanoplot.processed.stats_file
                )

        # Parse taxonomic abundances
        if self.config.results and self.config.results.enabled:
            sample_data.taxonomic_abundances = self._parse_rel_abundance()

            # Collect pipeline files
            sample_data.pipeline_files = self._collect_pipeline_files()

        return sample_data

    def _find_file(self, directory: str, filename: str) -> Optional[str]:
        """Find a file based on directory and filename."""
        file_path = self.seqrun_path / directory / filename
        if file_path.exists():
            return str(file_path.relative_to(self.seqrun_path))
        return None

    def _parse_nanoplot_stage(self, stage_config) -> Dict[str, str]:
        """Parse NanoPlot files for a stage (processed/unprocessed)."""
        html_files = {}

        for html_file in stage_config.html_files:
            file_path = self.seqrun_path / stage_config.directory / html_file
            if file_path.exists():
                html_files[html_file] = str(file_path.relative_to(self.seqrun_path))

        return html_files

    def _parse_nano_stats(self, directory: str, filename: str) -> Optional[NanoStats]:
        """Parse NanoStats.txt file."""
        stats_file = self.seqrun_path / directory / filename

        if not stats_file.exists():
            return None

        try:
            with open(stats_file, 'r') as f:
                content = f.read()

            # Parse the stats using regex
            stats = {}

            # Extract basic statistics
            patterns = {
                'mean_read_length': r'Mean read length:\s+([0-9,]+\.?[0-9]*)',
                'mean_read_quality': r'Mean read quality:\s+([0-9]+\.?[0-9]*)',
                'median_read_length': r'Median read length:\s+([0-9,]+\.?[0-9]*)',
                'median_read_quality': r'Median read quality:\s+([0-9]+\.?[0-9]*)',
                'number_of_reads': r'Number of reads:\s+([0-9,]+\.?[0-9]*)',
                'read_length_n50': r'Read length N50:\s+([0-9,]+\.?[0-9]*)',
                'stdev_read_length': r'STDEV read length:\s+([0-9,]+\.?[0-9]*)',
                'total_bases': r'Total bases:\s+([0-9,]+\.?[0-9]*)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1).replace(',', '')
                    if key == 'number_of_reads':
                        stats[key] = int(float(value))
                    else:
                        stats[key] = float(value)

            # Parse quality cutoffs
            quality_cutoffs = {}
            q_pattern = r'>Q(\d+):\s+(\d+)\s+\(([0-9.]+)%\)\s+([0-9.]+)Mb'
            for match in re.finditer(q_pattern, content):
                q_level = f"Q{match.group(1)}"
                count = int(match.group(2))
                percentage = float(match.group(3))
                megabases = float(match.group(4))
                quality_cutoffs[q_level] = (count, percentage, megabases)

            return NanoStats(
                quality_cutoffs=quality_cutoffs,
                **stats
            )

        except Exception as e:
            print(f"Error parsing NanoStats file {stats_file}: {e}")
            return None

    def _parse_rel_abundance(self) -> List[TaxonomicAbundance]:
        """Parse relative abundance TSV file."""
        if not self.config.results:
            return []

        abundance_file = self.seqrun_path / self.config.results.directory / self.config.results.rel_abundance_file

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

    def _collect_pipeline_files(self) -> List[str]:
        """Collect additional pipeline files for the sample."""
        pipeline_files = []

        # Add NanoPlot HTML files
        if self.config.nanoplot:
            for stage_name, stage_config in [
                ("unprocessed", self.config.nanoplot.unprocessed),
                ("processed", self.config.nanoplot.processed)
            ]:
                if stage_config and stage_config.enabled:
                    for html_file in stage_config.html_files:
                        file_path = self.seqrun_path / stage_config.directory / html_file
                        if file_path.exists():
                            pipeline_files.append(str(file_path.relative_to(self.seqrun_path)))

        return pipeline_files

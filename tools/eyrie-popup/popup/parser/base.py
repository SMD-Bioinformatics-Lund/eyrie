"""Main sample parser orchestration."""

from pathlib import Path

from ..models import SampleConfig, SampleData, ParsedSample
from ..utils import get_detected_spike, find_file
from .nanoplot import NanoPlotParser
from .nanostats import NanoStatsParser
from .taxonomic import TaxonomicParser


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
            sample_data.fastqc_file = find_file(
                self.seqrun_path,
                self.config.fastqc.directory,
                self.config.fastqc.file
            )

        # Parse Krona
        if self.config.krona and self.config.krona.enabled:
            sample_data.krona_file = find_file(
                self.seqrun_path,
                self.config.krona.directory,
                self.config.krona.file
            )

        # Parse MultiQC (shared across samples)
        if self.config.multiqc and self.config.multiqc.enabled:
            sample_data.multiqc_file = find_file(
                self.seqrun_path,
                self.config.multiqc.directory,
                self.config.multiqc.report_file
            )

        # Parse NanoPlot data
        if self.config.nanoplot:
            nanoplot_parser = NanoPlotParser(self.seqrun_path)

            if self.config.nanoplot.unprocessed and self.config.nanoplot.unprocessed.enabled:
                sample_data.nanoplot_unprocessed = nanoplot_parser.parse_stage(
                    self.config.nanoplot.unprocessed
                )

                nanostats_parser = NanoStatsParser(self.seqrun_path)
                sample_data.nano_stats_unprocessed = nanostats_parser.parse_nano_stats(
                    self.config.nanoplot.unprocessed.directory,
                    self.config.nanoplot.unprocessed.stats_file
                )

            if self.config.nanoplot.processed and self.config.nanoplot.processed.enabled:
                sample_data.nanoplot_processed = nanoplot_parser.parse_stage(
                    self.config.nanoplot.processed
                )

                nanostats_parser = NanoStatsParser(self.seqrun_path)
                sample_data.nano_stats_processed = nanostats_parser.parse_nano_stats(
                    self.config.nanoplot.processed.directory,
                    self.config.nanoplot.processed.stats_file
                )

            # Create structured nanoplot data
            sample_data.nanoplot = nanoplot_parser.create_structured_nanoplot(self.config.nanoplot)

        # Parse taxonomic abundances
        if self.config.results and self.config.results.enabled:
            taxonomic_parser = TaxonomicParser(self.seqrun_path)
            sample_data.taxonomic_abundances = taxonomic_parser.parse_rel_abundance(self.config.results)

            # Detect spike species after parsing taxonomic data
            spike = get_detected_spike(sample_data.taxonomic_abundances)
            if spike:
                sample_data.spike = spike

        return sample_data

"""Main sample parser orchestration."""

from pathlib import Path

from ..models import SampleConfig, SampleResults, ParsedSample
from ..utils import find_file
from .emu_metrics import existing_file, parse_classification_qc, parse_emu_metrics
from .nanoplot import NanoPlotParser
from .nanostats import NanoStatsParser
from .taxonomic import TaxonomicParser


class SampleParser:
    """Parser for single sample sequencing analysis outputs."""

    def __init__(self, config: SampleConfig):
        self.config = config
        self.analysis_output_path = Path(config.analysis_output_dirpath)
        self.seqrun_path = self.analysis_output_path

    def parse_sample(self) -> ParsedSample:
        """Parse the sample analysis data."""
        sample_data = self._parse_sample_data()
        return ParsedSample(sample_data=sample_data)

    def _parse_sample_data(self) -> SampleResults:
        """Parse data for the sample."""
        sample_data = SampleResults(sample_info=self.config.sample)

        if self.config.fastqc and self.config.fastqc.enabled:
            sample_data.fastqc_file = find_file(
                self.seqrun_path,
                self.config.fastqc.directory,
                self.config.fastqc.file
            )

        if self.config.krona and self.config.krona.enabled:
            sample_data.krona_file = find_file(
                self.seqrun_path,
                self.config.krona.directory,
                self.config.krona.file
            )

        if self.config.multiqc and self.config.multiqc.enabled:
            sample_data.multiqc_file = find_file(
                self.seqrun_path,
                self.config.multiqc.directory,
                self.config.multiqc.report_file
            )

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

            sample_data.nanoplot = nanoplot_parser.create_structured_nanoplot(self.config.nanoplot)

        if self.config.results and self.config.results.enabled:
            results_dir = self.seqrun_path / self.config.results.directory
            taxonomic_parser = TaxonomicParser(self.seqrun_path)
            sample_data.taxonomic_abundances = taxonomic_parser.parse_rel_abundance(self.config.results)
            parse_emu_metrics(sample_data.taxonomic_abundances, results_dir, self.config.results)

            if self.config.multiqc and self.config.multiqc.enabled:
                sample_data.classification_qc = parse_classification_qc(
                    existing_file(self.seqrun_path / self.config.multiqc.directory, self.config.multiqc.data_file),
                    existing_file(results_dir, self.config.results.emu_log_file),
                    self.config.sample.sample_id
                )

        return sample_data

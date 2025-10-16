"""NanoPlot parsing functionality."""

from pathlib import Path
from typing import Dict, Optional

from ..models import NanoPlotFileSet, StructuredNanoPlot


class NanoPlotParser:
    """Parser for NanoPlot files."""

    def __init__(self, seqrun_path: Path):
        self.seqrun_path = seqrun_path

    def parse_stage(self, stage_config) -> Dict[str, str]:
        """Parse NanoPlot files for a stage (processed/unprocessed)."""
        html_files = {}

        for html_file in stage_config.html_files:
            file_path = self.seqrun_path / stage_config.directory / html_file
            if file_path.exists():
                html_files[html_file] = str(file_path.relative_to(self.seqrun_path))

        return html_files

    def create_structured_nanoplot(self, nanoplot_config) -> Optional[StructuredNanoPlot]:
        """Create structured nanoplot file organization."""
        if not nanoplot_config:
            return None

        structured_nanoplot = StructuredNanoPlot()

        # Process unprocessed files
        if nanoplot_config.unprocessed and nanoplot_config.unprocessed.enabled:
            unprocessed_files = NanoPlotFileSet()
            for html_file in nanoplot_config.unprocessed.html_files:
                file_path = self.seqrun_path / nanoplot_config.unprocessed.directory / html_file
                if file_path.exists():
                    relative_path = str(file_path.relative_to(self.seqrun_path))
                    self._assign_file_to_structure(unprocessed_files, html_file, relative_path)
            structured_nanoplot.unprocessed = unprocessed_files

        # Process processed files
        if nanoplot_config.processed and nanoplot_config.processed.enabled:
            processed_files = NanoPlotFileSet()
            for html_file in nanoplot_config.processed.html_files:
                file_path = self.seqrun_path / nanoplot_config.processed.directory / html_file
                if file_path.exists():
                    relative_path = str(file_path.relative_to(self.seqrun_path))
                    self._assign_file_to_structure(processed_files, html_file, relative_path)
            structured_nanoplot.processed = processed_files

        return structured_nanoplot

    def _assign_file_to_structure(self, file_set: NanoPlotFileSet, filename: str, relative_path: str):
        """Assign a file to the appropriate field in the NanoPlotFileSet based on filename."""
        if 'NanoPlot-report.html' in filename:
            file_set.report = relative_path
        elif 'LengthvsQualityScatterPlot_dot.html' in filename:
            file_set.length_quality_scatter = relative_path
        elif 'LengthvsQualityScatterPlot_kde.html' in filename:
            file_set.length_quality_kde = relative_path
        elif 'Non_weightedHistogramReadlength.html' in filename:
            file_set.histogram_unweighted = relative_path
        elif 'WeightedHistogramReadlength.html' in filename:
            file_set.histogram_weighted = relative_path
        elif 'Yield_By_Length.html' in filename:
            file_set.yield_by_length = relative_path

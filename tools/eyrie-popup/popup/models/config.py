"""Configuration models for sample processing."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SampleInfo(BaseModel):
    """Information about individual samples."""
    sample_id: str
    sample_name: str
    lims_id: str
    sequencing_run_id: str
    classification_type: str = Field(..., regex="^(16S|ITS)$")
    barcode: Optional[str] = None


class FastQCConfig(BaseModel):
    """Configuration for FastQC files."""
    enabled: bool = True
    directory: str = "fastqc"
    file: str  # Direct file name instead of pattern


class KronaConfig(BaseModel):
    """Configuration for Krona files."""
    enabled: bool = True
    directory: str = "krona"
    file: str  # Direct file name instead of pattern


class MultiQCConfig(BaseModel):
    """Configuration for MultiQC files."""
    enabled: bool = True
    directory: str = "multiqc"
    report_file: str = "multiqc_report.html"


class NanoPlotStageConfig(BaseModel):
    """Configuration for a NanoPlot stage (processed/unprocessed)."""
    enabled: bool = True
    directory: str
    stats_file: str  # Direct file name instead of pattern
    html_files: List[str] = []


class NanoPlotConfig(BaseModel):
    """Configuration for NanoPlot files."""
    unprocessed: Optional[NanoPlotStageConfig] = None
    processed: Optional[NanoPlotStageConfig] = None


class ResultsConfig(BaseModel):
    """Configuration for analysis results."""
    enabled: bool = True
    directory: str = "results"
    rel_abundance_file: str  # Direct file name instead of pattern


class SampleConfig(BaseModel):
    """Complete sample configuration."""
    sample: SampleInfo
    base_path: str
    run_directory: Optional[str] = None
    fastqc: Optional[FastQCConfig] = None
    krona: Optional[KronaConfig] = None
    multiqc: Optional[MultiQCConfig] = None
    nanoplot: Optional[NanoPlotConfig] = None
    results: Optional[ResultsConfig] = None

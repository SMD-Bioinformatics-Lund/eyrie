"""Pydantic models for Eyrie POPUP (Pipeline Output Processor and UPloader)."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


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


class NanoStats(BaseModel):
    """Parsed NanoStats data."""
    mean_read_length: float
    mean_read_quality: float
    median_read_length: float
    median_read_quality: float
    number_of_reads: int
    read_length_n50: float
    stdev_read_length: float
    total_bases: int
    quality_cutoffs: Dict[str, tuple] = {}  # e.g., {"Q10": (count, percentage, megabases)}


class TaxonomicAbundance(BaseModel):
    """Taxonomic abundance data."""
    tax_id: str
    abundance: float
    species: str
    genus: str
    family: str
    order: str
    class_name: str = Field(..., alias="class")
    phylum: str
    superkingdom: str
    estimated_counts: float
    contamination: bool = False  # Will be added during parsing


class SampleData(BaseModel):
    """Complete data for a single sample."""
    sample_info: SampleInfo
    fastqc_file: Optional[str] = None
    krona_file: Optional[str] = None
    multiqc_file: Optional[str] = None
    nanoplot_unprocessed: Optional[Dict[str, str]] = None
    nanoplot_processed: Optional[Dict[str, str]] = None
    nano_stats_unprocessed: Optional[NanoStats] = None
    nano_stats_processed: Optional[NanoStats] = None
    taxonomic_abundances: List[TaxonomicAbundance] = []
    pipeline_files: List[str] = []


class ParsedSample(BaseModel):
    """Complete parsed sample data."""
    sample_data: SampleData
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)

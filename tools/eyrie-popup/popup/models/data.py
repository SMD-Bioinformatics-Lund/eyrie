"""Data models for parsed sample information."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from .config import SampleInfo


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
    nanoplot: Optional['StructuredNanoPlot'] = None
    spike: Optional[str] = None

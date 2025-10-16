"""Parsing-specific models."""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .data import SampleData


class NanoPlotFileSet(BaseModel):
    """Individual nanoplot files for processed or unprocessed data."""
    report: Optional[str] = None
    length_quality_scatter: Optional[str] = None
    length_quality_kde: Optional[str] = None
    histogram_unweighted: Optional[str] = None
    histogram_weighted: Optional[str] = None
    yield_by_length: Optional[str] = None


class StructuredNanoPlot(BaseModel):
    """Structured organization of nanoplot files."""
    unprocessed: Optional[NanoPlotFileSet] = None
    processed: Optional[NanoPlotFileSet] = None


class ParsedSample(BaseModel):
    """Complete parsed sample data."""
    sample_data: SampleData
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class QCUpdate(BaseModel):
    qc: str
    comments: Optional[str] = ""

class CommentUpdate(BaseModel):
    comments: str

class SpeciesFlagsUpdate(BaseModel):
    flagged_contaminants: Optional[List[str]] = None
    flagged_top_hits: Optional[List[str]] = None

class SampleCreate(BaseModel):
    sample_name: str
    sample_id: str
    sequencing_run_id: str
    lims_id: str
    classification: str = "16S"
    qc: str = "unprocessed"
    comments: str = ""
    krona_file: Optional[str] = None
    quality_plot: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    taxonomic_data: Optional[Dict[str, Any]] = None
    nano_stats_processed: Optional[Dict[str, Any]] = None
    nano_stats_unprocessed: Optional[Dict[str, Any]] = None
    flagged_contaminants: List[str] = []
    flagged_top_hits: List[str] = []
    nanoplot: Optional[Dict[str, Any]] = None
    spike: Optional[str] = None

class SampleUpdate(BaseModel):
    sample_name: Optional[str] = None
    lims_id: Optional[str] = None
    classification: Optional[str] = None
    qc: Optional[str] = None
    comments: Optional[str] = None
    krona_file: Optional[str] = None
    quality_plot: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    taxonomic_data: Optional[Dict[str, Any]] = None
    nano_stats_processed: Optional[Dict[str, Any]] = None
    nano_stats_unprocessed: Optional[Dict[str, Any]] = None
    flagged_contaminants: Optional[List[str]] = None
    flagged_top_hits: Optional[List[str]] = None
    nanoplot: Optional[Dict[str, Any]] = None
    spike: Optional[str] = None

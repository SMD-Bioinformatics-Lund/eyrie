from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class QCUpdate(BaseModel):
    qc: str
    comments: Optional[Dict[str, Any]] = None  # Updated to match new structure

class CommentUpdate(BaseModel):
    comments: Optional[Dict[str, Any]] = None  # Updated to match new structure

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
    comments: Optional[Dict[str, Any]] = None  # {"qc": [...], "other": "..."}
    files: Optional[Dict[str, Any]] = None  # {"krona": "...", "fastqc": "..."}
    sequencing_statistics: Optional[Dict[str, Any]] = None
    taxonomic_data: Optional[Dict[str, Any]] = None
    flagged_contaminants: List[str] = []
    flagged_top_hits: List[str] = []
    nanoplot: Optional[Dict[str, Any]] = None  # Now includes files and nanostats nested
    spike: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SampleUpdate(BaseModel):
    sample_name: Optional[str] = None
    lims_id: Optional[str] = None
    classification: Optional[str] = None
    qc: Optional[str] = None
    comments: Optional[Dict[str, Any]] = None  # {"qc": [...], "other": "..."}
    files: Optional[Dict[str, Any]] = None  # {"krona": "...", "fastqc": "..."}
    sequencing_statistics: Optional[Dict[str, Any]] = None
    taxonomic_data: Optional[Dict[str, Any]] = None
    flagged_contaminants: Optional[List[str]] = None
    flagged_top_hits: Optional[List[str]] = None
    nanoplot: Optional[Dict[str, Any]] = None  # Now includes files and nanostats nested
    spike: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class SequencingMetadata(BaseModel):
    """Sequencing run metadata from instrument report files."""
    exp_start_time: Optional[datetime] = None
    asic_id: Optional[str] = None
    asic_id_eeprom: Optional[str] = None
    asic_temp: Optional[str] = None
    asic_version: Optional[str] = None
    configuration_version: Optional[str] = None
    data_source: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    distribution_status: Optional[str] = None
    distribution_version: Optional[str] = None
    exp_script_name: Optional[str] = None
    exp_script_purpose: Optional[str] = None
    flow_cell_id: Optional[str] = None
    flow_cell_product_code: Optional[str] = None
    guppy_version: Optional[str] = None
    heatsink_temp: Optional[str] = None
    host_product_code: Optional[str] = None
    host_product_serial_number: Optional[str] = None
    hostname: Optional[str] = None
    installation_type: Optional[str] = None
    is_simulated: Optional[str] = None
    operating_system: Optional[str] = None
    protocol_group_id: Optional[str] = None
    protocol_run_id: Optional[str] = None
    protocol_start_time: Optional[str] = None
    protocols_version: Optional[str] = None
    run_id: Optional[str] = None
    sample_id: Optional[str] = None
    usb_config: Optional[str] = None
    version: Optional[str] = None

class PipelineFiles(BaseModel):
    execution_report: Optional[str] = None
    execution_timeline: Optional[str] = None
    pipeline_dag: Optional[str] = None

class PipelineParameterCategory(BaseModel):
    name: str
    parameters: Dict[str, Dict[str, Any]]

class PipelineParameters(BaseModel):
    trace_timestamp: Optional[str] = None
    categories: Dict[str, PipelineParameterCategory]
    total_parameters: int
    parsed_at: str

class ExecutionTaskSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_duration_seconds: int
    total_cpu_time_seconds: int
    max_memory_mb: float
    avg_duration_seconds: int
    avg_memory_mb: float

class ExecutionTask(BaseModel):
    task_id: str
    hash: Optional[str] = None
    native_id: Optional[str] = None
    name: str
    status: str
    exit_code: int
    submit_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    realtime_seconds: Optional[int] = None
    cpu_percentage: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    peak_vmem_mb: Optional[float] = None
    read_chars: Optional[str] = None
    write_chars: Optional[str] = None

class ExecutionTrace(BaseModel):
    tasks: List[ExecutionTask]
    summary: ExecutionTaskSummary
    parsed_at: str

class SoftwareToolCategory(BaseModel):
    name: str
    tools: Dict[str, Dict[str, Any]]

class SoftwareVersionsSummary(BaseModel):
    total_categories: int
    total_tools: int
    total_versions: int

class SoftwareVersions(BaseModel):
    categories: Dict[str, SoftwareToolCategory]
    workflow: Dict[str, str]
    summary: SoftwareVersionsSummary
    parsed_at: str

class SeqrunCreate(BaseModel):
    sequencing_run_id: str
    pipeline_software: str  # "trana" or "metaval"
    pipeline_files: Optional[PipelineFiles] = None
    pipeline_parameters: Optional[PipelineParameters] = None
    execution_trace: Optional[ExecutionTrace] = None
    software_versions: Optional[SoftwareVersions] = None
    created_date: Optional[datetime] = None
    sequencing_metadata: Optional[SequencingMetadata] = None

class SeqrunUpdate(BaseModel):
    pipeline_software: Optional[str] = None
    pipeline_files: Optional[PipelineFiles] = None
    pipeline_parameters: Optional[PipelineParameters] = None
    execution_trace: Optional[ExecutionTrace] = None
    software_versions: Optional[SoftwareVersions] = None
    updated_date: Optional[datetime] = None
    sequencing_metadata: Optional[SequencingMetadata] = None

class SeqrunResponse(BaseModel):
    sequencing_run_id: str
    pipeline_software: str
    pipeline_files: Optional[PipelineFiles] = None
    pipeline_parameters: Optional[PipelineParameters] = None
    execution_trace: Optional[ExecutionTrace] = None
    software_versions: Optional[SoftwareVersions] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    sequencing_metadata: Optional[SequencingMetadata] = None

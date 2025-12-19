from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from typing import List, Dict, Any
import os
import json
import glob
import re
from datetime import datetime
from eyrie_api.database.async_sample_operations import get_all_samples
from eyrie_api.routes.auth import get_current_user
from eyrie_api.utils.json_encoder import JSONEncoder

router = APIRouter(prefix="/seqruns", tags=["sequencing_runs"])

# Base path for pipeline_info directories - adjust based on your setup
PIPELINE_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "analysis-files", "results")

def parse_datetime_from_filename(filename: str) -> datetime:
    """Extract datetime from filename with format YYYY-MM-DD_HH-MM-SS"""
    match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
    if match:
        datetime_str = match.group(1)
        return datetime.strptime(datetime_str, '%Y-%m-%d_%H-%M-%S')
    return datetime.min

def get_latest_file_by_pattern(pipeline_path: str, pattern: str) -> str:
    """Get the latest file matching the pattern based on datetime in filename"""
    files = glob.glob(os.path.join(pipeline_path, pattern))
    if not files:
        return None

    # Sort by datetime extracted from filename
    files.sort(key=parse_datetime_from_filename, reverse=True)
    return files[0]

def get_seqrun_pipeline_path(seqrun_id: str) -> str:
    """Get the pipeline_info path for a sequencing run"""
    # Structure is: results/{seqrun_id}/pipeline_info
    pipeline_path = os.path.join(PIPELINE_BASE_PATH, seqrun_id, "pipeline_info")
    if not os.path.exists(pipeline_path):
        raise HTTPException(status_code=404, detail=f"Pipeline info not found for sequencing run: {seqrun_id}")
    return pipeline_path

def discover_sequencing_runs() -> List[str]:
    """Discover sequencing runs by scanning the filesystem"""
    seqruns = []
    try:
        if os.path.exists(PIPELINE_BASE_PATH):
            for item in os.listdir(PIPELINE_BASE_PATH):
                item_path = os.path.join(PIPELINE_BASE_PATH, item)
                # Check if it's a directory and has a pipeline_info subdirectory
                if os.path.isdir(item_path):
                    pipeline_info_path = os.path.join(item_path, "pipeline_info")
                    if os.path.exists(pipeline_info_path):
                        seqruns.append(item)
    except OSError:
        pass
    return sorted(seqruns)

async def get_seqrun_samples(seqrun_id: str) -> List[Dict[str, Any]]:
    """Get all samples for a specific sequencing run"""
    all_samples = await get_all_samples()
    seqrun_samples = [sample for sample in all_samples if sample.get('sequencing_run_id') == seqrun_id]
    return seqrun_samples

async def calculate_seqrun_stats(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate statistics for a sequencing run"""
    total_samples = len(samples)
    approved_samples = sum(1 for sample in samples if sample.get('qc') == 'approved')
    true_hits = sum(1 for sample in samples if sample.get('flagged_top_hits'))
    spikes_detected = sum(1 for sample in samples if sample.get('spike'))

    return {
        'total_samples': total_samples,
        'approved_samples': approved_samples,
        'true_hits': true_hits,
        'spikes_detected': spikes_detected
    }

@router.get("")
async def get_sequencing_runs(current_user: dict = Depends(get_current_user)):
    """Get list of all sequencing runs"""
    try:
        # Discover sequencing runs from filesystem
        discovered_seqruns = discover_sequencing_runs()

        # Get all samples to correlate with sequencing runs
        all_samples = await get_all_samples()

        # Group samples by sequencing run ID
        sample_data = {}
        for sample in all_samples:
            seqrun_id = sample.get('sequencing_run_id')
            if seqrun_id:
                if seqrun_id not in sample_data:
                    sample_data[seqrun_id] = []
                sample_data[seqrun_id].append(sample)

        # Build sequencing run data
        seqruns = []
        for seqrun_id in discovered_seqruns:
            samples = sample_data.get(seqrun_id, [])
            stats = await calculate_seqrun_stats(samples)

            # Get run metadata from first sample or use defaults
            first_sample = samples[0] if samples else None
            run_date = first_sample.get('sequencing_run_date') if first_sample else None
            created_date = first_sample.get('created_date') if first_sample else None

            seqrun_data = {
                'sequencing_run_id': seqrun_id,
                'run_date': run_date,
                'created_date': created_date,
                'pipeline_status': 'completed',
                **stats
            }

            seqruns.append(seqrun_data)

        # Sort by sequencing run ID (most recent first)
        seqruns.sort(key=lambda x: x.get('sequencing_run_id'), reverse=True)

        return json.loads(JSONEncoder().encode(seqruns))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}")
async def get_sequencing_run(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get details for a specific sequencing run"""
    try:
        # Get samples for this sequencing run
        samples = await get_seqrun_samples(seqrun_id)

        if not samples:
            raise HTTPException(status_code=404, detail=f"Sequencing run not found: {seqrun_id}")

        # Calculate stats
        stats = await calculate_seqrun_stats(samples)

        # Get run metadata from first sample
        first_sample = samples[0]

        seqrun = {
            'sequencing_run_id': seqrun_id,
            'run_date': first_sample.get('sequencing_run_date'),
            'created_date': first_sample.get('created_date'),
            'pipeline_status': 'completed',
            'samples': samples,
            **stats
        }

        return json.loads(JSONEncoder().encode(seqrun))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}/execution-report")
async def get_execution_report(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get the latest execution report HTML file"""
    try:
        pipeline_path = get_seqrun_pipeline_path(seqrun_id)
        report_file = get_latest_file_by_pattern(pipeline_path, "execution_report_*.html")

        if not report_file:
            raise HTTPException(status_code=404, detail="Execution report not found")

        return FileResponse(report_file, media_type='text/html')

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}/execution-timeline")
async def get_execution_timeline(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get the latest execution timeline HTML file"""
    try:
        pipeline_path = get_seqrun_pipeline_path(seqrun_id)
        timeline_file = get_latest_file_by_pattern(pipeline_path, "execution_timeline_*.html")

        if not timeline_file:
            raise HTTPException(status_code=404, detail="Execution timeline not found")

        return FileResponse(timeline_file, media_type='text/html')

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}/execution-trace")
async def get_execution_trace(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get the latest execution trace text file"""
    try:
        pipeline_path = get_seqrun_pipeline_path(seqrun_id)
        trace_file = get_latest_file_by_pattern(pipeline_path, "execution_trace_*.txt")

        if not trace_file:
            raise HTTPException(status_code=404, detail="Execution trace not found")

        with open(trace_file, 'r') as f:
            content = f.read()

        return PlainTextResponse(content, media_type='text/plain')

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}/params")
async def get_params(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get the latest params JSON file"""
    try:
        pipeline_path = get_seqrun_pipeline_path(seqrun_id)
        params_file = get_latest_file_by_pattern(pipeline_path, "params_*.json")

        if not params_file:
            raise HTTPException(status_code=404, detail="Parameters file not found")

        with open(params_file, 'r') as f:
            params_data = json.load(f)

        return params_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{seqrun_id}/software-versions")
async def get_software_versions(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get the software versions YAML file"""
    try:
        pipeline_path = get_seqrun_pipeline_path(seqrun_id)
        versions_file = os.path.join(pipeline_path, "software_versions.yml")

        if not os.path.exists(versions_file):
            raise HTTPException(status_code=404, detail="Software versions file not found")

        with open(versions_file, 'r') as f:
            content = f.read()

        return PlainTextResponse(content, media_type='text/plain')

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
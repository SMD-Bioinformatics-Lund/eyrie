from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import json
from eyrie_api.database.async_sample_operations import (
    get_all_samples, get_contamination_analysis, update_sample_species_flags,
    get_qc_overview_analysis, get_read_quality_analysis, get_taxonomic_diversity_analysis,
    get_outlier_detection_analysis, get_positive_control_validation
)
from eyrie_api.database.async_seqrun_operations import upsert_seqrun, find_seqrun, get_all_seqruns
from eyrie_api.models.seqruns import SeqrunCreate
from eyrie_api.routes.auth import get_current_user
from eyrie_api.utils.json_encoder import JSONEncoder

router = APIRouter(prefix="/seqruns", tags=["sequencing_runs"])


async def get_seqrun_samples(seqrun_id: str) -> List[Dict[str, Any]]:
    """Get all samples for a specific sequencing run"""
    all_samples = await get_all_samples()
    seqrun_samples = [sample for sample in all_samples if sample.get('sequencing_run_id') == seqrun_id]
    return seqrun_samples

async def calculate_seqrun_stats(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate statistics for a sequencing run"""
    total_samples = len(samples)
    approved_samples = sum(1 for sample in samples if sample.get('qc') == 'passed')
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
        # Get all samples to correlate with sequencing runs
        all_samples = await get_all_samples()

        # Group samples by sequencing run ID from samples
        sample_data = {}
        sample_seqrun_ids = set()
        for sample in all_samples:
            seqrun_id = sample.get('sequencing_run_id')
            if seqrun_id:
                sample_seqrun_ids.add(seqrun_id)
                if seqrun_id not in sample_data:
                    sample_data[seqrun_id] = []
                sample_data[seqrun_id].append(sample)

        all_seqrun_ids = sample_seqrun_ids

        # Get seqrun metadata from MongoDB collection for richer data
        all_seqrun_docs = await get_all_seqruns()
        seqruns_dict = {doc.get('sequencing_run_id'): doc for doc in all_seqrun_docs}

        # Build sequencing run data
        seqruns = []
        for seqrun_id in all_seqrun_ids:
            samples = sample_data.get(seqrun_id, [])
            stats = await calculate_seqrun_stats(samples)

            first_sample = samples[0] if samples else None
            created_date = first_sample.get('created_date') if first_sample else None

            # Get seqrun document if available
            seqrun_doc = seqruns_dict.get(seqrun_id)

            if seqrun_doc and isinstance(seqrun_doc, dict):
                # Extract metadata from nested structure for compatibility
                sequencing_metadata = seqrun_doc.get('sequencing_metadata', {})
                if not isinstance(sequencing_metadata, dict):
                    sequencing_metadata = {}

                seqrun_data = {
                    'sequencing_run_id': seqrun_id,
                    'created_date': seqrun_doc.get('created_date', created_date),
                    'pipeline_status': 'completed',
                    'pipeline_software': seqrun_doc.get('pipeline_software'),
                    'exp_start_time': sequencing_metadata.get('exp_start_time'),
                    'device_id': sequencing_metadata.get('device_id'),
                    'flow_cell_id': sequencing_metadata.get('flow_cell_id'),
                    'hostname': sequencing_metadata.get('hostname'),
                    **stats
                }
            else:
                # Fallback for seqruns without metadata documents
                seqrun_data = {
                    'sequencing_run_id': seqrun_id,
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
        # First try to get seqrun from MongoDB collection
        seqrun_doc = await find_seqrun(seqrun_id)

        # Get samples for this sequencing run
        samples = await get_seqrun_samples(seqrun_id)

        if not samples and not seqrun_doc:
            raise HTTPException(status_code=404, detail=f"Sequencing run not found: {seqrun_id}")

        # Calculate stats from samples
        stats = await calculate_seqrun_stats(samples)

        if seqrun_doc and isinstance(seqrun_doc, dict):
            # Use seqrun data from MongoDB collection
            # Extract sequencing metadata for compatibility
            sequencing_metadata = seqrun_doc.get('sequencing_metadata', {})
            if not isinstance(sequencing_metadata, dict):
                sequencing_metadata = {}

            seqrun = {
                'sequencing_run_id': seqrun_doc.get('sequencing_run_id', seqrun_id),
                'exp_start_time': sequencing_metadata.get('exp_start_time'),
                'created_date': seqrun_doc.get('created_date'),
                'pipeline_status': 'completed',
                'pipeline_software': seqrun_doc.get('pipeline_software'),
                'pipeline_files': seqrun_doc.get('pipeline_files', {}),
                'pipeline_parameters': seqrun_doc.get('pipeline_parameters'),
                'execution_trace': seqrun_doc.get('execution_trace'),
                'software_versions': seqrun_doc.get('software_versions'),
                'device_id': sequencing_metadata.get('device_id'),
                'flow_cell_id': sequencing_metadata.get('flow_cell_id'),
                'hostname': sequencing_metadata.get('hostname'),
                'protocol_group_id': sequencing_metadata.get('protocol_group_id'),
                'sequencing_metadata': sequencing_metadata,
                'samples': samples,
                **stats
            }
        else:
            first_sample = samples[0] if samples else {}
            seqrun = {
                'sequencing_run_id': seqrun_id,
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

@router.put("/{seqrun_id}")
async def upsert_sequencing_run(seqrun_id: str, seqrun_data: SeqrunCreate, current_user: dict = Depends(get_current_user)):
    """Create or update sequencing run data"""
    try:
        # Ensure the seqrun_id in URL matches the data
        if seqrun_data.sequencing_run_id != seqrun_id:
            raise HTTPException(status_code=400, detail="Sequencing run ID mismatch")

        # Convert Pydantic model to dict with proper nested serialization
        seqrun_dict = seqrun_data.dict(by_alias=True, exclude_unset=False)
        result_id, was_created = await upsert_seqrun(seqrun_dict)

        status_code = 201 if was_created else 200
        action = "created" if was_created else "updated"

        return {"message": f"Sequencing run {action} successfully", "id": result_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/contamination")
async def get_seqrun_contamination_analysis(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get contamination analysis for a specific sequencing run"""
    try:
        contamination_data = await get_contamination_analysis(seqrun_id)
        return json.loads(JSONEncoder().encode(contamination_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/qc/overview")
async def get_seqrun_qc_overview(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get QC overview analysis for a specific sequencing run"""
    try:
        qc_data = await get_qc_overview_analysis(seqrun_id)
        return json.loads(JSONEncoder().encode(qc_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/qc/read-quality")
async def get_seqrun_read_quality(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get read quality analysis for a specific sequencing run"""
    try:
        quality_data = await get_read_quality_analysis(seqrun_id)
        return json.loads(JSONEncoder().encode(quality_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/qc/taxonomic-diversity")
async def get_seqrun_taxonomic_diversity(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get taxonomic diversity analysis for a specific sequencing run"""
    try:
        diversity_data = await get_taxonomic_diversity_analysis(seqrun_id)
        return json.loads(JSONEncoder().encode(diversity_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/qc/outlier-detection")
async def get_seqrun_outlier_detection(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get outlier detection analysis for a specific sequencing run"""
    try:
        outlier_data = await get_outlier_detection_analysis(seqrun_id)
        return json.loads(JSONEncoder().encode(outlier_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/qc/positive-controls")
async def get_seqrun_positive_control_validation(seqrun_id: str, current_user: dict = Depends(get_current_user)):
    """Get positive control validation for a specific sequencing run"""
    try:
        validation_data = await get_positive_control_validation(seqrun_id)
        return json.loads(JSONEncoder().encode(validation_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seqrun_id}/flag-contamination")
async def flag_species_as_contamination(seqrun_id: str, species_name: str, current_user: dict = Depends(get_current_user)):
    """Flag a species as contamination across all samples in the sequencing run"""
    try:
        # Get all samples in this sequencing run
        all_samples = await get_all_samples()
        seqrun_samples = [sample for sample in all_samples if sample.get('sequencing_run_id') == seqrun_id]

        if not seqrun_samples:
            raise HTTPException(status_code=404, detail=f"No samples found for sequencing run: {seqrun_id}")

        flagged_count = 0

        # Process each sample in the sequencing run
        for sample in seqrun_samples:
            sample_id = sample.get('sample_id')
            if not sample_id:
                continue

            # Check if this sample has the specified species in taxonomic data
            taxonomic_data = sample.get('taxonomic_data', {})
            hits = taxonomic_data.get('hits', [])

            # Look for the species in the taxonomic hits
            species_found = False
            for hit in hits:
                if hit.get('species', '').strip() == species_name.strip():
                    species_found = True
                    break

            if species_found:
                # Get current flagged contaminants
                current_contaminants = sample.get('flagged_contaminants', [])

                # Add species to contaminants if not already flagged
                if species_name not in current_contaminants:
                    updated_contaminants = current_contaminants + [species_name]

                    # Update the sample with the new flagged contaminant
                    success = await update_sample_species_flags(
                        sample_id, 
                        flagged_contaminants=updated_contaminants,
                        flagged_top_hits=sample.get('flagged_top_hits')  # Keep existing top hits
                    )

                    if success:
                        flagged_count += 1

        return {
            "message": f"Successfully flagged '{species_name}' as contamination in {flagged_count} sample(s)",
            "flagged_samples": flagged_count,
            "total_samples": len(seqrun_samples),
            "species_name": species_name,
            "seqrun_id": seqrun_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

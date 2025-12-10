import json
from fastapi import APIRouter, HTTPException, Depends
from eyrie_api.models.samples import QCUpdate, CommentUpdate, SampleCreate, SampleUpdate, SpeciesFlagsUpdate
from eyrie_api.database.async_sample_operations import (
    find_sample, update_sample_qc, update_sample_comment,
    update_sample, upsert_sample, update_sample_species_flags,
    find_negative_controls_by_run_id
)
from eyrie_api.routes.auth import require_admin_or_uploader
from eyrie_api.utils.json_encoder import JSONEncoder

router = APIRouter(prefix="/sample", tags=["sample"])

@router.get("/{sample_id}")
async def get_sample(sample_id: str):
    try:
        sample = await find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        return json.loads(JSONEncoder().encode(sample))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}")
async def upsert_sample_endpoint(
    sample_id: str,
    sample_data: SampleCreate,
    current_user: dict = Depends(require_admin_or_uploader)
):
    """Create or update a sample (requires admin or uploader role)"""
    try:
        if sample_data.sample_id != sample_id:
            raise HTTPException(
                status_code=400, 
                detail="Sample ID in URL must match sample ID in data"
            )

        sample_dict = sample_data.dict(exclude_unset=False, exclude_none=False)
        db_id, was_created = await upsert_sample(sample_dict)

        action = "created" if was_created else "updated"
        return {
            "message": f"Sample '{sample_id}' {action} successfully",
            "sample_id": sample_id,
            "database_id": db_id,
            "created": was_created
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{sample_id}")
async def partial_update_sample(
    sample_id: str,
    sample_data: SampleUpdate,
    current_user: dict = Depends(require_admin_or_uploader)
):
    """Partially update a sample (requires admin or uploader role)"""
    try:
        update_dict = sample_data.dict(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No data provided for update")

        success = await update_sample(sample_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {
            "message": f"Sample '{sample_id}' updated successfully",
            "updated_fields": list(update_dict.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/qc")
async def update_qc(
    sample_id: str,
    qc_data: QCUpdate
):
    """Update sample QC status"""
    try:
        if qc_data.qc not in ['passed', 'failed', 'unprocessed']:
            raise HTTPException(status_code=400, detail="Invalid QC status")

        success = await update_sample_qc(sample_id, qc_data.qc, qc_data.comments)
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/comment")
async def update_comment(
    sample_id: str,
    comment_data: CommentUpdate
):
    """Update sample comment"""
    try:
        success = await update_sample_comment(sample_id, comment_data.comments)
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/species-flags")
async def update_species_flags(
    sample_id: str,
    species_flags_data: SpeciesFlagsUpdate
):
    """Update sample species flags (contaminants and/or top hits)"""
    try:
        success = await update_sample_species_flags(
            sample_id,
            species_flags_data.flagged_contaminants,
            species_flags_data.flagged_top_hits
        )
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sample_id}/negative-controls")
async def get_negative_controls(sample_id: str):
    """Get negative control samples from the same sequencing run"""
    try:
        # First, get the main sample to find its sequencing_run_id
        sample = await find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        sequencing_run_id = sample.get('sequencing_run_id')
        if not sequencing_run_id:
            return []  # Return empty list if no sequencing_run_id
        
        # Find negative controls for this sequencing run
        negative_controls = await find_negative_controls_by_run_id(sequencing_run_id)
        
        return json.loads(JSONEncoder().encode(negative_controls))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
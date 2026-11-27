import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from eyrie_api.models.samples import QCUpdate, CommentUpdate, CategoryUpdate, SampleCreate, SampleUpdate, SpeciesFlagsUpdate
from eyrie_api.database.async_sample_operations import (
    find_sample, update_sample_qc, update_sample_comment, update_sample_category,
    update_sample, upsert_sample, update_sample_species_flags,
    find_negative_controls_by_run_id
)
from eyrie_api.database.async_settings_operations import get_spike_settings
from eyrie_api.routes.auth import require_admin, require_admin_or_uploader, get_current_user
from eyrie_api.utils.classification import classify_sample, comparison_controls, detected_spike
from eyrie_api.utils.json_encoder import JSONEncoder

router = APIRouter(prefix="/sample", tags=["sample"])


async def run_negative_controls(sample):
    sequencing_run_id = sample.get('sequencing_run_id')
    if not sequencing_run_id:
        return []
    return await find_negative_controls_by_run_id(sequencing_run_id, sample.get('classification'))


@router.get("/{sample_id}")
async def get_sample(sample_id: str):
    try:
        sample = await find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        sample['spike'] = detected_spike(sample, (await get_spike_settings())['species'])
        return json.loads(JSONEncoder().encode(sample))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}")
async def upsert_sample_endpoint(
    sample_id: str,
    sample_data: SampleCreate,
    reset_review: bool = False,
    current_user: dict = Depends(require_admin_or_uploader)
):
    """Create a sample, or replace its pipeline results keeping QC, comments, flags, metadata and LIMS ID.
    With reset_review, QC status, comments and flags are replaced too (requires admin or uploader role)"""
    try:
        if sample_data.sample_id != sample_id:
            raise HTTPException(
                status_code=400, 
                detail="Sample ID in URL must match sample ID in data"
            )

        sample_dict = sample_data.model_dump()
        db_id, was_created = await upsert_sample(sample_dict, current_user['username'], reset_review)

        action = "created" if was_created else "updated"
        return {
            "message": f"Sample '{sample_id}' {action} successfully",
            "sample_id": sample_id,
            "database_id": db_id,
            "created": was_created
        }
    except HTTPException:
        raise
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
    qc_data: QCUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update sample QC status"""
    try:
        if qc_data.qc not in ['passed', 'failed', 'unprocessed']:
            raise HTTPException(status_code=400, detail="Invalid QC status")

        success = await update_sample_qc(sample_id, qc_data.qc, qc_data.comment, current_user['username'])
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        response = {'success': True}
        if qc_data.comment:
            response['comment'] = {
                'user': current_user['username'],
                'timestamp': datetime.now().isoformat(),
                'comment': qc_data.comment
            }
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/category")
async def update_category(
    sample_id: str,
    category_data: CategoryUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update sample category"""
    if not await update_sample_category(sample_id, category_data.category):
        raise HTTPException(status_code=404, detail="Sample not found")
    return {'success': True}

@router.put("/{sample_id}/comment")
async def update_comment(
    sample_id: str,
    comment_data: CommentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update sample comment"""
    try:
        success = await update_sample_comment(
            sample_id, comment_data.qc_comment, comment_data.other, current_user['username']
        )
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        response = {'success': True}
        if comment_data.qc_comment:
            response['comment'] = {
                'user': current_user['username'],
                'timestamp': datetime.now().isoformat(),
                'comment': comment_data.qc_comment
            }
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/species-flags")
async def update_species_flags(
    sample_id: str,
    species_flags_data: SpeciesFlagsUpdate,
    current_user: dict = Depends(get_current_user)
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
    """Get the negative controls from the same sequencing run that the sample is compared with"""
    try:
        # First, get the main sample to find its sequencing_run_id
        sample = await find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")

        controls, _ = comparison_controls(sample, await run_negative_controls(sample))
        return json.loads(JSONEncoder().encode(controls))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sample_id}/classification")
async def get_classification(sample_id: str, current_user: dict = Depends(get_current_user)):
    """Get taxonomic hits flagged against the run's negative controls and spike species"""
    try:
        sample = await find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")

        classification = classify_sample(sample, await run_negative_controls(sample), await get_spike_settings())

        return json.loads(JSONEncoder().encode(classification))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

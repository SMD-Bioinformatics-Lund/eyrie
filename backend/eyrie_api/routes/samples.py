from fastapi import APIRouter, HTTPException
from eyrie_api.models.samples import QCUpdate, CommentUpdate
from eyrie_api.database.sample_operations import get_all_samples, find_sample, update_sample_qc, update_sample_comment
from eyrie_api.utils.json_encoder import JSONEncoder
import json

router = APIRouter(prefix="/api/samples", tags=["samples"])

@router.get("")
async def get_samples():
    try:
        samples = get_all_samples()
        return json.loads(JSONEncoder().encode(samples))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sample_id}")
async def get_sample(sample_id: str):
    try:
        sample = find_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        return json.loads(JSONEncoder().encode(sample))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/qc")
async def update_qc(sample_id: str, qc_data: QCUpdate):
    try:
        if qc_data.qc not in ['passed', 'failed', 'unprocessed']:
            raise HTTPException(status_code=400, detail="Invalid QC status")

        success = update_sample_qc(sample_id, qc_data.qc, qc_data.comments)
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sample_id}/comment")
async def update_comment(sample_id: str, comment_data: CommentUpdate):
    try:
        success = update_sample_comment(sample_id, comment_data.comments)
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Depends
from eyrie_api.models.samples import SampleCreate
from eyrie_api.database.async_sample_operations import (
    get_all_samples, create_sample
)
from eyrie_api.routes.auth import require_admin_or_uploader, get_current_user
from eyrie_api.utils.json_encoder import JSONEncoder
import json

router = APIRouter(prefix="/samples", tags=["samples"])

@router.get("")
async def get_samples(current_user: dict = Depends(get_current_user)):
    try:
        samples = await get_all_samples()
        return json.loads(JSONEncoder().encode(samples))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_new_sample(
    sample_data: SampleCreate, 
    current_user: dict = Depends(require_admin_or_uploader)
):
    """Create a new sample (requires admin or uploader role)"""
    try:
        sample_dict = sample_data.dict(exclude_unset=False, exclude_none=False)
        sample_id = await create_sample(sample_dict)
        return {
            "message": f"Sample '{sample_data.sample_id}' created successfully",
            "sample_id": sample_data.sample_id,
            "database_id": sample_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter(tags=["frontend"])

@router.get("/data/{file_path:path}")
async def serve_data_file(file_path: str):
    file_full_path = f"/app/data/{file_path}"
    if os.path.exists(file_full_path):
        return FileResponse(file_full_path)
    raise HTTPException(status_code=404, detail="File not found")

@router.get("/health")
async def health_check():
    try:
        from eyrie_api.database.connection import db
        db.samples.count_documents({})
        return {'status': 'healthy'}
    except Exception as e:
        raise HTTPException(status_code=500, detail={'status': 'unhealthy', 'error': str(e)})

@router.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse('frontend/blueprints/samples/templates/index.html')

@router.get("/samples", response_class=HTMLResponse)
async def samples_page():
    return FileResponse('frontend/blueprints/samples/templates/index.html')

@router.get("/sample/{sample_id}", response_class=HTMLResponse)
async def sample_detail(sample_id: str):
    return FileResponse('frontend/blueprints/sample/templates/detail.html')

@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return FileResponse('frontend/blueprints/admin/templates/dashboard.html')

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse('frontend/blueprints/login/templates/index.html')

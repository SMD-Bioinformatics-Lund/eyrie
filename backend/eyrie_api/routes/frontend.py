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
    return {
        'status': 'healthy',
        'service': 'eyrie-backend',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'database_required': False  # Health check doesn't require DB connection
    }

@router.get("/")
async def root():
    """Backend API root - redirect to docs"""
    return {
        "message": "Eyrie Sample Manager API",
        "version": "0.2.1",
        "documentation": "/docs",
        "health": "/health"
    }

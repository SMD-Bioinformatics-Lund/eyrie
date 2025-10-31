from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

# Data files router - for serving HTML reports, plots, etc.
data_router = APIRouter(prefix="/files", tags=["files"])

@data_router.get("/data/{file_path:path}")
async def serve_data_file(file_path: str):
    """Serve data files (HTML reports, plots, etc.)"""
    file_full_path = f"/app/data/{file_path}"
    if os.path.exists(file_full_path):
        return FileResponse(file_full_path)
    raise HTTPException(status_code=404, detail="File not found")

# System/health router - for health checks, system info, etc.
system_router = APIRouter(prefix="/system", tags=["system"])

@system_router.get("/health")
async def health_check():
    """System health check"""
    return {
        'status': 'healthy',
        'service': 'eyrie-backend',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'database_required': False
    }

@system_router.get("/info")
async def system_info():
    """System information"""
    return {
        "message": "Eyrie Sample Manager API",
        "version": "0.2.1",
        "documentation": "/docs",
        "health": "/api/system/health",
        "api_endpoints": {
            "auth": "/api/auth",
            "samples": "/api/samples",
            "sample": "/api/sample",
            "admin": "/api/admin",
            "trends": "/api/trends",
            "files": "/api/files"
        }
    }

@system_router.get("/debug")
async def debug_info():
    """Debug information for troubleshooting"""
    try:
        import sys
        import platform
        
        return {
            "status": "running",
            "service": "eyrie-backend",
            "python_version": sys.version,
            "platform": platform.platform(),
            "environment_variables": {
                "ENVIRONMENT": os.getenv('ENVIRONMENT'),
                "MONGO_URI": os.getenv('MONGO_URI', 'not_set')[:50] + "..." if os.getenv('MONGO_URI') else "not_set",
                "PYTHONPATH": os.getenv('PYTHONPATH'),
            },
            "working_directory": os.getcwd(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@system_router.get("/test")
async def simple_test():
    """Simple test endpoint to verify backend is alive"""
    return {"message": "Backend is alive", "status": "ok"}

# API root router - no longer needed since we handle /api directly in main.py
# api_router = APIRouter(prefix="/api", tags=["api"])

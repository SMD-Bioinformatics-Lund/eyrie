from fastapi import APIRouter
import os
import sys
import platform

from eyrie_api.__version__ import __version__

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
        "version": __version__,
        "documentation": "/docs",
        "health": "/api/system/health",
        "api_endpoints": {
            "auth": "/api/auth",
            "samples": "/api/samples",
            "sample": "/api/sample",
            "admin": "/api/admin",
            "trends": "/api/trends",
        }
    }

@system_router.get("/debug")
async def debug_info():
    """Debug information for troubleshooting"""
    try:
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

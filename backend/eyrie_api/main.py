from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from eyrie_api.config.settings import (
    APP_TITLE, APP_HOST, APP_PORT,
    CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
)
from eyrie_api.database.utils import init_default_user, close_database
from eyrie_api.routes import admin, samples, frontend, auth, trends

logger = logging.getLogger(__name__)

app = FastAPI(title=APP_TITLE)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

@app.on_event("startup")
async def startup_event():
    """Minimal startup without database initialization to avoid threading issues"""
    try:
        logger.info("=== BACKEND STARTUP BEGINNING ===")
        logger.info("Application startup - skipping database initialization to avoid threading issues")
        logger.info("Database initialization will be performed lazily on first request")
        
        # Test basic functionality without database
        import os
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
        logger.info(f"MongoDB URI configured: {'MONGO_URI' in os.environ}")
        
        logger.info("=== BACKEND STARTUP COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize application: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't raise to allow graceful degradation
        logger.warning("Application started but some initialization tasks failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    try:
        logger.info("Closing database connections...")
        await close_database()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Basic health check endpoint (no database dependency)
@app.get("/health")
async def health_check():
    """Basic health check without database dependency"""
    try:
        import os
        return {
            "status": "healthy",
            "service": "eyrie-backend",
            "environment": os.getenv('ENVIRONMENT', 'unknown'),
            "database_required": False
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/simple-test")
async def simple_test():
    """Ultra simple test endpoint"""
    return {"message": "Backend is alive", "status": "ok"}

@app.get("/debug")
async def debug_info():
    """Debug information for troubleshooting"""
    try:
        import os
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
            "app_title": APP_TITLE,
        }
    except Exception as e:
        logger.error(f"Debug endpoint failed: {e}")
        return {"status": "error", "error": str(e)}

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(samples.router)
app.include_router(trends.router)
app.include_router(frontend.router)

# Mount static file directories
# app.mount("/shared/static", StaticFiles(directory="frontend/shared/static"), name="shared_static")
# app.mount("/blueprints", StaticFiles(directory="frontend/blueprints"), name="blueprints")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)

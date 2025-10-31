from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from eyrie_api.config.settings import (
    APP_TITLE, APP_HOST, APP_PORT,
    CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
)
from eyrie_api.database.utils import init_default_user, close_database
from eyrie_api.routes import admin, samples, sample, frontend, auth, trends

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

@app.get("/")
async def root():
    """Root endpoint - redirect to API documentation"""
    return {
        "message": "Eyrie Sample Manager Backend",
        "version": "0.2.1",
        "api": "/api",
        "documentation": "/docs",
        "health": "/api/system/health"
    }

@app.get("/api")
async def api_root_no_slash():
    """API root endpoint without trailing slash"""
    return {
        "message": "Eyrie Sample Manager API",
        "version": "0.2.1",
        "documentation": "/docs",
        "health": "/api/system/health",
        "endpoints": {
            "auth": "/api/auth",
            "samples": "/api/samples",
            "sample": "/api/sample",
            "admin": "/api/admin", 
            "trends": "/api/trends",
            "files": "/api/files",
            "system": "/api/system"
        }
    }


# Include API routers (now they have /api prefix built into their paths due to updated prefixes)
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(samples.router, prefix="/api")
app.include_router(sample.router, prefix="/api")
app.include_router(trends.router, prefix="/api")

# Include system and file routers
app.include_router(frontend.system_router, prefix="/api")
app.include_router(frontend.data_router, prefix="/api")

# Mount static file directories
# app.mount("/shared/static", StaticFiles(directory="frontend/shared/static"), name="shared_static")
# app.mount("/blueprints", StaticFiles(directory="frontend/blueprints"), name="blueprints")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)

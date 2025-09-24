from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.settings import (
    APP_TITLE, APP_HOST, APP_PORT,
    CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
)
from database.connection import init_default_user
from routes import auth, admin, samples, frontend

app = FastAPI(title=APP_TITLE)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# Initialize default user on startup
init_default_user()

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(samples.router)
app.include_router(frontend.router)

# Mount static file directories
app.mount("/shared/static", StaticFiles(directory="frontend/shared/static"), name="shared_static")
app.mount("/blueprints", StaticFiles(directory="frontend/blueprints"), name="blueprints")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)

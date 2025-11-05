from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import os
from config import settings
from database import engine, Base

# Import routes
from routes import (
    map_routes,
    rating_routes,
    indicator_routes,
    methodology_routes,
    upload_routes,
)

# Setup logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Log startup info
logger.info("Starting Reyting Dashboard API")
logger.info(f"Environment: DEBUG={os.getenv('DEBUG', 'false')}")
logger.info(f"ALLOWED_ORIGINS={os.getenv('ALLOWED_ORIGINS', '*')}")

# Create tables
logger.info("Creating database tables if not exist...")
Base.metadata.create_all(bind=engine)
logger.info("✓ Database tables ready")

# Create app with /api docs path
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

# Configure CORS from environment (narrow CORS for production security)
# ALLOWED_ORIGINS should be comma-separated list of domains (NOT wildcard for production)
# Example: https://reyting-frontend-alex1976.amvera.io,https://reyting-alex1976.amvera.io
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "https://localhost:3000")
cors_origins = [o.strip() for o in allowed_origins_str.split(",")]

logger.info(f"✓ CORS configured for {len(cors_origins)} origin(s)")
for origin in cors_origins:
    logger.info(f"  - {origin}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint (root level for container healthchecks)
@app.get("/health")
async def health_check():
    """Health check endpoint for Amvera/K8s probes"""
    return {"status": "ok", "service": "reyting-api"}


# Root endpoint (redirect to API docs)
@app.get("/")
async def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/api/docs")


# API info endpoint
@app.get("/api")
async def api_info():
    """API information and endpoints"""
    return {
        "service": "Reyting Dashboard API",
        "version": settings.api_version,
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
        "health": "/health",
        "endpoints": {
            "rating": "/api/rating",
            "indicators": "/api/indicators",
            "map": "/api/map",
            "methodology": "/api/methodology",
            "upload": "/api/upload",
        }
    }


# Include routers
app.include_router(map_routes.router, prefix="/api/map", tags=["map"])
app.include_router(rating_routes.router, prefix="/api/rating", tags=["rating"])
app.include_router(indicator_routes.router, prefix="/api/indicators", tags=["indicators"])
app.include_router(methodology_routes.router, prefix="/api/methodology", tags=["methodology"])
app.include_router(upload_routes.router, prefix="/api/upload", tags=["upload"])


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)

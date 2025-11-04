from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "message": "Dashboard API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
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

"""
FastAPI application for fitlog cloud backend.

This API provides REST endpoints that mirror the CLI functionality,
supporting the same operations but via HTTP instead of local database.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# We'll import from V1 models
import sys
sys.path.append('..')
from fitlog.models import Run, Pushup

# Import routers
from .routers import runs, pushups, activities

app = FastAPI(
    title="Fitlog Cloud API",
    description="REST API for tracking daily exercise habits with cloud storage",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(pushups.router, prefix="/pushups", tags=["pushups"])
app.include_router(activities.router, prefix="/activities", tags=["activities"])

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Fitlog Cloud API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "healthy",
        "endpoints": {
            "runs": "/runs",
            "pushups": "/pushups", 
            "activities": "/activities",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
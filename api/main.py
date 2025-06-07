"""
FastAPI application for fitlog cloud backend.

This API provides REST endpoints that mirror the CLI functionality,
supporting the same operations but via HTTP instead of local database.
"""

import os

# We'll import from V1 models
import sys
from datetime import datetime

from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel

sys.path.append("..")

app = FastAPI(
    title="Fitlog API",
    description="Personal exercise tracking API - Cloud Version",
    version="2.0.0",
)


# Pydantic models for API
class RunCreate(BaseModel):
    duration: str  # HH:MM:SS format
    distance: float  # miles
    date: str | None = None  # MM/DD/YY format


class PushupCreate(BaseModel):
    count: int
    date: str | None = None  # MM/DD/YY format


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "message": "🏃‍♂️ Fitlog API v2.0.0 - Cloud Edition",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "s3_bucket": os.getenv("S3_BUCKET", "unknown"),
        "lambda_function": os.getenv("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/runs")
async def get_runs():
    """Get all runs - TODO: implement with DuckDB S3"""
    return {
        "message": "Get runs endpoint - ready for DuckDB S3 implementation",
        "data": [],
        "todo": [
            "Connect to DuckDB on S3",
            "Query runs from cloud database",
            "Return paginated results",
        ],
    }


@app.post("/runs")
async def create_run(run: RunCreate):
    """Create a new run - TODO: implement with DuckDB S3"""
    return {
        "message": "Create run endpoint - ready for DuckDB S3 implementation",
        "received_data": {
            "duration": run.duration,
            "distance": run.distance,
            "date": run.date or datetime.now().strftime("%m/%d/%y"),
        },
        "todo": [
            "Validate run data with fitlog.models.Run",
            "Store in DuckDB on S3",
            "Return created run with ID",
        ],
    }


@app.get("/pushups")
async def get_pushups():
    """Get all pushups - TODO: implement with DuckDB S3"""
    return {
        "message": "Get pushups endpoint - ready for DuckDB S3 implementation",
        "data": [],
        "todo": [
            "Connect to DuckDB on S3",
            "Query pushups from cloud database",
            "Return paginated results",
        ],
    }


@app.post("/pushups")
async def create_pushup(pushup: PushupCreate):
    """Create new pushup entry - TODO: implement with DuckDB S3"""
    return {
        "message": "Create pushup endpoint - ready for DuckDB S3 implementation",
        "received_data": {
            "count": pushup.count,
            "date": pushup.date or datetime.now().strftime("%m/%d/%y"),
        },
        "todo": [
            "Validate pushup data with fitlog.models.Pushup",
            "Store in DuckDB on S3",
            "Return created pushup with ID",
        ],
    }


@app.get("/activities/status")
async def get_activity_status():
    """Get activity status and statistics - TODO: implement with DuckDB S3"""
    return {
        "message": "Activity status endpoint - ready for DuckDB S3 implementation",
        "status": "placeholder",
        "stats": {"total_runs": 0, "total_pushups": 0, "current_streak": 0},
        "todo": [
            "Connect to DuckDB on S3",
            "Calculate real statistics",
            "Return activity streaks and goals",
        ],
    }


@app.get("/test")
async def test_endpoint():
    """Test endpoint for GitHub Actions deployment verification"""
    return {
        "test": "success",
        "message": "🎉 GitHub Actions deployment working!",
        "environment_vars": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
            "S3_BUCKET": os.getenv("S3_BUCKET"),
            "DUCKDB_PATH": os.getenv("DUCKDB_PATH"),
            "AWS_REGION": os.getenv("AWS_DEFAULT_REGION"),
        },
        "lambda_context": {
            "function_name": os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            "function_version": os.getenv("AWS_LAMBDA_FUNCTION_VERSION"),
            "memory_limit": os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"),
        },
    }


# Lambda handler for AWS
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

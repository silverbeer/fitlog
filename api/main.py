"""
FastAPI application for fitlog cloud backend.

This API provides REST endpoints that mirror the CLI functionality,
supporting the same operations but via HTTP instead of local database.
"""

import os
import sys
from datetime import datetime, time

from fastapi import FastAPI, HTTPException, Query
from mangum import Mangum
from pydantic import BaseModel, Field

# Import our cloud database and models
sys.path.append("..")
from db_cloud import CloudDatabase
from fitlog.models import Pushup, Run

app = FastAPI(
    title="Fitlog API",
    description="Personal exercise tracking API - Cloud Version",
    version="2.0.0",
)


# Pydantic models for API requests
class RunCreate(BaseModel):
    duration: str = Field(..., description="Duration in HH:MM:SS format")
    distance: float = Field(..., gt=0, description="Distance in miles")
    date: str | None = Field(None, description="Date in MM/DD/YY format (optional)")


class PushupCreate(BaseModel):
    count: int = Field(..., gt=0, description="Number of pushups")
    date: str | None = Field(None, description="Date in MM/DD/YY format (optional)")


# Helper functions
def parse_duration(duration_str: str) -> time:
    """Parse duration string (HH:MM:SS) to time object."""
    try:
        parts = duration_str.split(":")
        if len(parts) != 3:
            raise ValueError("Duration must be in HH:MM:SS format")

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])

        # Validate ranges
        if hours >= 24:
            raise ValueError(
                "Duration hours must be less than 24. For longer activities, please break them into multiple entries."
            )
        if minutes >= 60:
            raise ValueError("Duration minutes must be less than 60")
        if seconds >= 60:
            raise ValueError("Duration seconds must be less than 60")
        if hours < 0 or minutes < 0 or seconds < 0:
            raise ValueError("Duration values must be non-negative")

        return time(hour=hours, minute=minutes, second=seconds)

    except ValueError as e:
        # Re-raise ValueError with our custom message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid duration format: {str(e)}"
        )


def parse_date(date_str: str | None) -> datetime:
    """Parse date string (MM/DD/YY) to datetime object."""
    if not date_str:
        return datetime.now()

    try:
        # Handle MM/DD/YY format
        if "/" in date_str:
            return datetime.strptime(date_str, "%m/%d/%y")
        # Handle YYYY-MM-DD format
        elif "-" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%d")
        else:
            raise ValueError("Date must be in MM/DD/YY or YYYY-MM-DD format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")


def get_db() -> CloudDatabase:
    """Get database instance with debug enabled in development."""
    debug = os.getenv("ENVIRONMENT", "production") != "production"
    return CloudDatabase(debug=debug)


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "message": "🏃‍♂️ Fitlog API v2.0.0 - Cloud Edition",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "s3_bucket": os.getenv("S3_BUCKET", "unknown"),
        "lambda_function": os.getenv("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
        "duckdb_path": os.getenv("DUCKDB_PATH", "unknown"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/runs", response_model=list[dict])
async def get_runs(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, le=1000, description="Maximum number of runs to return"),
):
    """Get runs from the database with optional date filtering."""
    try:
        db = get_db()

        # Parse date parameters
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Get runs from database
        runs = db.get_runs(start_date=start_dt, end_date=end_dt, limit=limit)

        # Convert to dict format for JSON response
        runs_data = []
        for run in runs:
            run_dict = {
                "activity_id": run.activity_id,
                "date": (
                    run.date.isoformat()
                    if isinstance(run.date, datetime)
                    else str(run.date)
                ),
                "duration": str(run.duration),
                "distance_miles": run.distance_miles,
                "pace_per_mile": str(run.pace_per_mile) if run.pace_per_mile else None,
                "heart_rate_avg": run.heart_rate_avg,
                "heart_rate_max": run.heart_rate_max,
                "heart_rate_min": run.heart_rate_min,
                "cadence_avg": run.cadence_avg,
                "cadence_max": run.cadence_max,
                "cadence_min": run.cadence_min,
                "temperature": run.temperature,
                "weather_type": run.weather_type,
                "humidity": run.humidity,
                "wind_speed": run.wind_speed,
                "splits": [
                    {
                        "mile_number": split.mile_number,
                        "duration": str(split.duration),
                        "pace": str(split.pace),
                        "heart_rate_avg": split.heart_rate_avg,
                        "cadence_avg": split.cadence_avg,
                    }
                    for split in (run.splits or [])
                ],
            }
            runs_data.append(run_dict)

        db.close()

        return runs_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get runs: {str(e)}")


@app.post("/runs", response_model=dict)
async def create_run(run_data: RunCreate):
    """Create a new run in the database."""
    try:
        db = get_db()

        # Parse input data
        duration = parse_duration(run_data.duration)
        date = parse_date(run_data.date)

        # Create Run object
        run = Run(
            date=date,
            duration=duration,
            distance_miles=run_data.distance,
        )

        # Save to database
        created_run = db.create_run(run)

        db.close()

        return {
            "message": "Run created successfully",
            "run": {
                "activity_id": created_run.activity_id,
                "date": created_run.date.isoformat(),
                "duration": str(created_run.duration),
                "distance_miles": created_run.distance_miles,
                "pace_per_mile": str(created_run.pace_per_mile),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")


@app.get("/pushups", response_model=list[dict])
async def get_pushups(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(
        100, le=1000, description="Maximum number of pushup entries to return"
    ),
):
    """Get pushups from the database with optional date filtering."""
    try:
        db = get_db()

        # Parse date parameters
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Get pushups from database
        pushups = db.get_pushups(start_date=start_dt, end_date=end_dt, limit=limit)

        # Convert to dict format for JSON response
        pushups_data = [
            {
                "date": (
                    pushup.date.isoformat()
                    if isinstance(pushup.date, datetime)
                    else str(pushup.date)
                ),
                "count": pushup.count,
            }
            for pushup in pushups
        ]

        db.close()

        return pushups_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pushups: {str(e)}")


@app.post("/pushups", response_model=dict)
async def create_pushup(pushup_data: PushupCreate):
    """Create a new pushup entry in the database."""
    try:
        db = get_db()

        # Parse input data
        date = parse_date(pushup_data.date)

        # Create Pushup object
        pushup = Pushup(
            date=date,
            count=pushup_data.count,
        )

        # Save to database
        created_pushup = db.create_pushup(pushup)

        db.close()

        return {
            "message": "Pushup entry created successfully",
            "pushup": {
                "date": created_pushup.date.isoformat(),
                "count": created_pushup.count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create pushup: {str(e)}"
        )


@app.get("/activities/status", response_model=dict)
async def get_activity_status(
    days: int = Query(30, le=365, description="Number of days to analyze")
):
    """Get activity status and statistics."""
    try:
        db = get_db()

        # Get statistics from database
        stats = db.get_stats(days=days)

        db.close()

        return {
            "message": "Activity status retrieved successfully",
            "stats": stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get activity status: {str(e)}"
        )


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

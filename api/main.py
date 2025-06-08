"""
FastAPI application for fitlog cloud backend.

This API provides REST endpoints that mirror the CLI functionality,
supporting the same operations but via HTTP instead of local database.
Enhanced with AWS Lambda Powertools for production-ready observability.
"""

import os
import sys
from datetime import datetime, time

# AWS Lambda Powertools for observability
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from mangum import Mangum
from pydantic import BaseModel, Field

# Import our cloud database and models
sys.path.append("..")
from db_cloud import CloudDatabase
from fitlog.models import Pushup, Run

# Initialize Powertools
logger = Logger(service="fitlog-api")
tracer = Tracer(service="fitlog-api")
metrics = Metrics(namespace="Fitlog", service="fitlog-api")

app = FastAPI(
    title="Fitlog API",
    description="Personal exercise tracking API - Cloud Version with AWS Powertools",
    version="2.0.0",
)


# Authentication
@tracer.capture_method
async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for authentication"""
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        logger.error("API key not configured on server")
        metrics.add_metric(name="AuthConfigError", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail="API key not configured on server")

    if not x_api_key:
        logger.warning("API key missing from request", extra={"endpoint": "auth"})
        metrics.add_metric(name="AuthMissingKey", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=401, detail="API key required. Include 'X-API-Key' header."
        )

    if x_api_key != expected_key:
        logger.warning(
            "Invalid API key provided",
            extra={
                "key_prefix": (
                    x_api_key[:8] + "..." if len(x_api_key) > 8 else "short_key"
                )
            },
        )
        metrics.add_metric(name="AuthInvalidKey", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.debug("API key authentication successful")
    metrics.add_metric(name="AuthSuccess", unit=MetricUnit.Count, value=1)
    return True


# Pydantic models for API requests
class RunCreate(BaseModel):
    duration: str = Field(..., description="Duration in HH:MM:SS format")
    distance: float = Field(..., gt=0, description="Distance in miles")
    date: str | None = Field(None, description="Date in MM/DD/YY format (optional)")


class PushupCreate(BaseModel):
    count: int = Field(..., gt=0, description="Number of pushups")
    date: str | None = Field(None, description="Date in MM/DD/YY format (optional)")


# Helper functions
@tracer.capture_method
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
                "Duration hours must be less than 24. For ultra-marathons, consider logging in segments."
            )
        if minutes >= 60:
            raise ValueError("Duration minutes must be less than 60")
        if seconds >= 60:
            raise ValueError("Duration seconds must be less than 60")
        if hours < 0 or minutes < 0 or seconds < 0:
            raise ValueError("Duration values must be non-negative")

        logger.debug(
            "Duration parsed successfully",
            extra={
                "duration_str": duration_str,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
            },
        )

        return time(hour=hours, minute=minutes, second=seconds)

    except ValueError as e:
        logger.error(
            "Duration parsing failed",
            extra={"duration_str": duration_str, "error": str(e)},
        )
        metrics.add_metric(name="DurationParseError", unit=MetricUnit.Count, value=1)
        # Re-raise ValueError with our custom message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Unexpected duration parsing error",
            extra={"duration_str": duration_str, "error": str(e)},
        )
        metrics.add_metric(name="DurationParseError", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=400, detail=f"Invalid duration format: {str(e)}"
        )


@tracer.capture_method
def parse_date(date_str: str | None) -> datetime:
    """Parse date string (MM/DD/YY) to datetime object."""
    if not date_str:
        return datetime.now()

    try:
        # Handle MM/DD/YY format
        if "/" in date_str:
            parsed_date = datetime.strptime(date_str, "%m/%d/%y")
        # Handle YYYY-MM-DD format
        elif "-" in date_str:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            raise ValueError("Date must be in MM/DD/YY or YYYY-MM-DD format")

        logger.debug(
            "Date parsed successfully",
            extra={"date_str": date_str, "parsed_date": parsed_date.isoformat()},
        )

        return parsed_date

    except Exception as e:
        logger.error(
            "Date parsing failed", extra={"date_str": date_str, "error": str(e)}
        )
        metrics.add_metric(name="DateParseError", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")


@tracer.capture_method
def get_db() -> CloudDatabase:
    """Get database instance with debug enabled in development."""
    debug = os.getenv("ENVIRONMENT", "production") != "production"
    logger.debug("Creating database connection", extra={"debug_mode": debug})
    return CloudDatabase(debug=debug)


@app.get("/")
@tracer.capture_method
async def health_check():
    """Health check endpoint - public access"""
    logger.info("Health check requested")
    metrics.add_metric(name="HealthCheck", unit=MetricUnit.Count, value=1)

    health_data = {
        "message": "🏃‍♂️ Fitlog API v2.0.0 - Cloud Edition with Powertools",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "s3_bucket": os.getenv("S3_BUCKET", "unknown"),
        "lambda_function": os.getenv("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
        "duckdb_path": os.getenv("DUCKDB_PATH", "unknown"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "powertools": {"logger": "enabled", "tracer": "enabled", "metrics": "enabled"},
    }

    logger.info("Health check completed", extra=health_data)
    return health_data


@app.get("/runs", response_model=list[dict], dependencies=[Depends(verify_api_key)])
@tracer.capture_method
async def get_runs(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, le=1000, description="Maximum number of runs to return"),
):
    """Get runs from the database with optional date filtering."""
    logger.info(
        "Getting runs",
        extra={"start_date": start_date, "end_date": end_date, "limit": limit},
    )

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

        logger.info(
            "Runs retrieved successfully",
            extra={
                "run_count": len(runs),
                "date_range": (
                    f"{start_date} to {end_date}" if start_date or end_date else "all"
                ),
            },
        )

        metrics.add_metric(name="RunsRetrieved", unit=MetricUnit.Count, value=len(runs))
        metrics.add_metric(name="GetRunsRequest", unit=MetricUnit.Count, value=1)

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
        logger.error("Failed to get runs", extra={"error": str(e)}, exc_info=True)
        metrics.add_metric(name="GetRunsError", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail=f"Failed to get runs: {str(e)}")


@app.post("/runs", response_model=dict, dependencies=[Depends(verify_api_key)])
@tracer.capture_method
async def create_run(run_data: RunCreate):
    """Create a new run in the database."""
    logger.info(
        "Creating new run",
        extra={
            "duration": run_data.duration,
            "distance": run_data.distance,
            "date": run_data.date,
        },
    )

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

        logger.info(
            "Run created successfully",
            extra={
                "activity_id": created_run.activity_id,
                "date": created_run.date.isoformat(),
                "distance": created_run.distance_miles,
            },
        )

        metrics.add_metric(name="RunCreated", unit=MetricUnit.Count, value=1)
        metrics.add_metric(
            name="DistanceLogged", unit=MetricUnit.Count, value=run_data.distance
        )

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
        logger.error("Failed to create run", extra={"error": str(e)}, exc_info=True)
        metrics.add_metric(name="CreateRunError", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")


@app.get("/pushups", response_model=list[dict], dependencies=[Depends(verify_api_key)])
@tracer.capture_method
async def get_pushups(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(
        100, le=1000, description="Maximum number of pushup entries to return"
    ),
):
    """Get pushups from the database with optional date filtering."""
    logger.info(
        "Getting pushups",
        extra={"start_date": start_date, "end_date": end_date, "limit": limit},
    )

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

        logger.info(
            "Pushups retrieved successfully",
            extra={
                "pushup_count": len(pushups),
                "date_range": (
                    f"{start_date} to {end_date}" if start_date or end_date else "all"
                ),
            },
        )

        metrics.add_metric(
            name="PushupsRetrieved", unit=MetricUnit.Count, value=len(pushups)
        )
        metrics.add_metric(name="GetPushupsRequest", unit=MetricUnit.Count, value=1)

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
        logger.error("Failed to get pushups", extra={"error": str(e)}, exc_info=True)
        metrics.add_metric(name="GetPushupsError", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail=f"Failed to get pushups: {str(e)}")


@app.post("/pushups", response_model=dict, dependencies=[Depends(verify_api_key)])
@tracer.capture_method
async def create_pushup(pushup_data: PushupCreate):
    """Create a new pushup entry in the database."""
    logger.info(
        "Creating new pushup entry",
        extra={"count": pushup_data.count, "date": pushup_data.date},
    )

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

        logger.info(
            "Pushup entry created successfully",
            extra={
                "date": created_pushup.date.isoformat(),
                "count": created_pushup.count,
            },
        )

        metrics.add_metric(name="PushupCreated", unit=MetricUnit.Count, value=1)
        metrics.add_metric(
            name="PushupCountLogged", unit=MetricUnit.Count, value=pushup_data.count
        )

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
        logger.error("Failed to create pushup", extra={"error": str(e)}, exc_info=True)
        metrics.add_metric(name="CreatePushupError", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=500, detail=f"Failed to create pushup: {str(e)}"
        )


@app.get(
    "/activities/status", response_model=dict, dependencies=[Depends(verify_api_key)]
)
@tracer.capture_method
async def get_activity_status(
    days: int = Query(30, le=365, description="Number of days to analyze")
):
    """Get activity status and statistics."""
    logger.info("Getting activity status", extra={"days": days})

    try:
        db = get_db()

        # Get statistics from database
        stats = db.get_stats(days=days)

        logger.info(
            "Activity status retrieved successfully",
            extra={
                "days_analyzed": days,
                "stats_keys": (
                    list(stats.keys()) if isinstance(stats, dict) else "non-dict"
                ),
            },
        )

        metrics.add_metric(name="ActivityStatusRequest", unit=MetricUnit.Count, value=1)

        db.close()

        return {
            "message": "Activity status retrieved successfully",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            "Failed to get activity status", extra={"error": str(e)}, exc_info=True
        )
        metrics.add_metric(name="ActivityStatusError", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=500, detail=f"Failed to get activity status: {str(e)}"
        )


@app.get("/test", dependencies=[Depends(verify_api_key)])
@tracer.capture_method
async def test_endpoint():
    """Test endpoint for GitHub Actions deployment verification"""
    logger.info("Test endpoint accessed")
    metrics.add_metric(name="TestEndpoint", unit=MetricUnit.Count, value=1)

    return {
        "test": "success",
        "message": "🎉 GitHub Actions deployment working with Powertools!",
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
        "powertools": {
            "service": "fitlog-api",
            "namespace": "Fitlog",
            "logger": "enabled",
            "tracer": "enabled",
            "metrics": "enabled",
        },
    }


# Lambda handler for AWS with Powertools decorators
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext):
    """Lambda handler with full Powertools integration"""
    logger.info(
        "Lambda handler invoked",
        extra={
            "event_source": event.get("requestContext", {}).get("stage", "unknown"),
            "http_method": event.get("httpMethod", "unknown"),
            "path": event.get("path", "unknown"),
        },
    )

    return Mangum(app)(event, context)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

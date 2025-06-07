"""
Runs router for fitlog cloud API.

Provides endpoints for logging runs and retrieving run history,
mirroring the CLI commands: log-run, get-run, etc.
"""

import sys
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

sys.path.append("../..")
from fitlog.models import Run

router = APIRouter()

# TODO: Import cloud database module
# from ..database import CloudDatabase
# db = CloudDatabase()


@router.post("/", response_model=dict)
async def log_run(run: Run):
    """
    Log a new run - equivalent to 'fitlog log-run' CLI command.

    Body should contain:
    - date: datetime
    - duration: time
    - distance_miles: float
    - Optional: heart_rate_avg, cadence_avg, etc.
    """
    try:
        # TODO: Implement DuckDB S3 storage
        # result = await db.log_run(run)

        # For now, return success response
        return {
            "status": "success",
            "message": f"Logged run: {run.distance_miles} miles in {run.duration}",
            "run_id": run.activity_id,
            "date": run.date.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log run: {str(e)}")


@router.get("/", response_model=list[Run])
async def get_runs(
    days: int = Query(1, description="Number of days back to retrieve runs"),
    start_date: str | None = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="End date in YYYY-MM-DD format"),
):
    """
    Get runs from the database - equivalent to 'fitlog get-run' CLI command.

    Query parameters:
    - days: Number of days back to look (default: 1)
    - start_date: Optional start date
    - end_date: Optional end date
    """
    try:
        # Calculate date range if not provided
        if not start_date and not end_date:
            end_date_dt = datetime.now()
            start_date_dt = end_date_dt - timedelta(days=days)
        else:
            if start_date:
                start_date_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_date_dt = datetime.fromisoformat(end_date)

        # TODO: Implement DuckDB S3 retrieval
        # runs = await db.get_runs(start_date_dt, end_date_dt)

        # For now, return empty list
        return []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve runs: {str(e)}"
        )


@router.get("/{run_id}")
async def get_run_by_id(run_id: int):
    """Get a specific run by its activity ID."""
    try:
        # TODO: Implement run retrieval by ID
        # run = await db.get_run_by_id(run_id)
        # if not run:
        #     raise HTTPException(status_code=404, detail="Run not found")
        # return run

        return {"message": f"Get run {run_id} - not implemented yet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve run: {str(e)}")


@router.delete("/{run_id}")
async def delete_run(run_id: int):
    """Delete a specific run by its activity ID."""
    try:
        # TODO: Implement run deletion
        # success = await db.delete_run(run_id)
        # if not success:
        #     raise HTTPException(status_code=404, detail="Run not found")

        return {"status": "success", "message": f"Run {run_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {str(e)}")

import os
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv

from fitlog.smashrun import SmashrunClient

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def client():
    """Create a Smashrun client using the token from environment variables."""
    token = os.getenv("SMASHRUN_ACCESS_TOKEN")
    if not token:
        pytest.skip("SMASHRUN_ACCESS_TOKEN not set in environment")
    return SmashrunClient(token)

def test_get_runs_yesterday(client):
    """Test fetching runs from yesterday."""
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Fetch runs
    runs = client.get_runs(start_date, end_date)

    # Basic validation
    assert isinstance(runs, list), "get_runs should return a list"

    # If there were any runs yesterday, validate their structure
    for run in runs:
        assert run is not None, "Run should not be None"
        assert run.date.date() == yesterday.date(), f"Run date should be yesterday, got {run.date}"
        assert run.distance_miles > 0, f"Distance should be positive, got {run.distance_miles}"
        assert run.duration is not None, "Duration should not be None"

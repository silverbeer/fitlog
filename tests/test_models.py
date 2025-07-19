"""
Unit tests for the fitlog models.

These tests don't require external APIs and test the core model functionality.
"""

from datetime import datetime, time

import pytest
from pydantic import ValidationError

from fitlog.models import Pushup, Run, Split


class TestRunModel:
    """Test the Run model validation and functionality."""

    def test_create_valid_run(self):
        """Test creating a valid run."""
        run = Run(duration=time(hour=0, minute=30, second=15), distance_miles=3.2)

        assert run.duration == time(hour=0, minute=30, second=15)
        assert run.distance_miles == 3.2
        assert isinstance(run.date, datetime)
        assert run.pace_per_mile is not None

    def test_run_pace_calculation(self):
        """Test that pace is calculated correctly."""
        # 30 minutes for 3 miles = 10 minutes per mile
        run = Run(duration=time(hour=0, minute=30, second=0), distance_miles=3.0)

        assert run.pace_per_mile == time(minute=10, second=0)

    def test_run_invalid_distance(self):
        """Test that negative distance raises validation error."""
        with pytest.raises(ValidationError):
            Run(duration=time(hour=0, minute=30), distance_miles=-1.0)

    def test_run_zero_distance(self):
        """Test that zero distance raises validation error."""
        with pytest.raises(ValidationError):
            Run(duration=time(hour=0, minute=30), distance_miles=0.0)

    def test_run_with_optional_fields(self):
        """Test creating a run with optional fields."""
        run = Run(
            duration=time(hour=0, minute=25, second=30),
            distance_miles=2.5,
            heart_rate_avg=145,
            cadence_avg=180,
            temperature=72.0,
            weather_type="sunny",
        )

        assert run.heart_rate_avg == 145
        assert run.cadence_avg == 180
        assert run.temperature == 72.0
        assert run.weather_type == "sunny"


class TestPushupModel:
    """Test the Pushup model validation and functionality."""

    def test_create_valid_pushup(self):
        """Test creating a valid pushup entry."""
        pushup = Pushup(count=50)

        assert pushup.count == 50
        assert isinstance(pushup.date, datetime)

    def test_pushup_invalid_count(self):
        """Test that negative count raises validation error."""
        with pytest.raises(ValidationError):
            Pushup(count=-10)

    def test_pushup_zero_count(self):
        """Test that zero count raises validation error."""
        with pytest.raises(ValidationError):
            Pushup(count=0)

    def test_pushup_with_custom_date(self):
        """Test creating a pushup with custom date."""
        custom_date = datetime(2025, 6, 1, 10, 30)
        pushup = Pushup(count=75, date=custom_date)

        assert pushup.count == 75
        assert pushup.date == custom_date


class TestSplitModel:
    """Test the Split model validation and functionality."""

    def test_create_valid_split(self):
        """Test creating a valid split."""
        split = Split(
            mile_number=1,
            duration=time(minute=8, second=30),
            pace=time(minute=8, second=30),
        )

        assert split.mile_number == 1
        assert split.duration == time(minute=8, second=30)
        assert split.pace == time(minute=8, second=30)

    def test_split_with_optional_fields(self):
        """Test creating a split with optional fields."""
        split = Split(
            mile_number=2,
            duration=time(minute=8, second=45),
            pace=time(minute=8, second=45),
            heart_rate_avg=150,
            cadence_avg=185,
        )

        assert split.heart_rate_avg == 150
        assert split.cadence_avg == 185

    def test_split_invalid_mile_number(self):
        """Test that zero or negative mile number raises validation error."""
        with pytest.raises(ValidationError):
            Split(
                mile_number=0,  # Should be > 0
                duration=time(minute=8, second=30),
                pace=time(minute=8, second=30),
            )

from datetime import datetime, time

from pydantic import BaseModel, Field, field_validator


class Split(BaseModel):
    mile_number: int = Field(gt=0)
    duration: time
    pace: time
    heart_rate_avg: int | None = None
    cadence_avg: int | None = None


class Run(BaseModel):
    activity_id: int | None = None
    date: datetime = Field(default_factory=datetime.now)
    duration: time
    distance_miles: float = Field(gt=0)
    pace_per_mile: time | None = None
    heart_rate_avg: int | None = None
    heart_rate_max: int | None = None
    heart_rate_min: int | None = None
    cadence_avg: int | None = None
    cadence_max: int | None = None
    cadence_min: int | None = None
    temperature: float | None = None
    weather_type: str | None = None
    humidity: int | None = None
    wind_speed: int | None = None
    splits: list[Split] | None = None

    @field_validator("distance_miles")
    @classmethod
    def validate_distance(cls, v):
        if v <= 0:
            raise ValueError("Distance must be positive")
        return v

    def calculate_pace(self) -> time:
        """Calculate pace per mile in MM:SS format"""
        # Convert duration to total seconds
        total_seconds = (
            self.duration.hour * 3600 + self.duration.minute * 60 + self.duration.second
        )
        # Calculate seconds per mile
        seconds_per_mile = total_seconds / self.distance_miles
        # Convert to minutes and seconds
        minutes = int(seconds_per_mile // 60)
        seconds = int(seconds_per_mile % 60)
        return time(minute=minutes, second=seconds)

    def __init__(self, **data):
        super().__init__(**data)
        self.pace_per_mile = self.calculate_pace()


class Pushup(BaseModel):
    date: datetime = Field(default_factory=datetime.now)
    count: int = Field(gt=0)

    @field_validator("count")
    @classmethod
    def validate_count(cls, v):
        if v <= 0:
            raise ValueError("Count must be positive")
        return v

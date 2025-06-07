from datetime import datetime, time, timedelta
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class Split(BaseModel):
    mile_number: int = Field(gt=0)
    duration: time
    pace: time
    heart_rate_avg: Optional[int] = None
    cadence_avg: Optional[int] = None

class Run(BaseModel):
    activity_id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.now)
    duration: time
    distance_miles: float = Field(gt=0)
    pace_per_mile: Optional[time] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    heart_rate_min: Optional[int] = None
    cadence_avg: Optional[int] = None
    cadence_max: Optional[int] = None
    cadence_min: Optional[int] = None
    temperature: Optional[float] = None
    weather_type: Optional[str] = None
    humidity: Optional[int] = None
    wind_speed: Optional[int] = None
    splits: Optional[List[Split]] = None
    
    @validator('distance_miles')
    def validate_distance(cls, v):
        if v <= 0:
            raise ValueError('Distance must be positive')
        return v
    
    def calculate_pace(self) -> time:
        """Calculate pace per mile in MM:SS format"""
        # Convert duration to total seconds
        total_seconds = self.duration.hour * 3600 + self.duration.minute * 60 + self.duration.second
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
    
    @validator('count')
    def validate_count(cls, v):
        if v <= 0:
            raise ValueError('Count must be positive')
        return v 
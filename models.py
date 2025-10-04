from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime


class WeatherPlanningRequest(BaseModel):
    """Request model for weather planning"""
    city: str = Field(..., description="City name")
    event: str = Field(..., description="Event type")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(2025, ge=2020, le=2026, description="Year")
    limit: int = Field(5, ge=1, le=5, description="Number of best days to return")

    @validator('city')
    def validate_city(cls, v):
        return v.strip().title()

    @validator('event')
    def validate_event(cls, v):
        return v.strip().lower()


class WeatherDay(BaseModel):
    """Model for a single weather day"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    score: float = Field(..., description="Weather suitability score (0-100)")
    temp_celsius: float = Field(..., description="Temperature in Celsius")
    precip: float = Field(..., description="Precipitation in mm")
    wind_max_speed: float = Field(..., description="Maximum wind speed in m/s")
    humidity_afternoon: float = Field(..., description="Afternoon humidity percentage")
    cloud_cover_afternoon: float = Field(..., description="Afternoon cloud cover percentage")


class WeatherPlanningResponse(BaseModel):
    """Response model for weather planning"""
    success: bool = Field(..., description="Request success status")
    city: str = Field(..., description="Requested city")
    event: str = Field(..., description="Requested event")
    month: int = Field(..., description="Requested month")
    year: int = Field(..., description="Requested year")
    best_days: List[WeatherDay] = Field(..., description="List of best days for the event")
    message: Optional[str] = Field(None, description="Additional message")


class AvailableOptionsResponse(BaseModel):
    """Response model for available cities and events"""
    cities: List[str] = Field(..., description="Available cities")
    events: List[str] = Field(..., description="Available events")


class EventCriteria(BaseModel):
    """Model for event criteria"""
    temp_range: tuple[float, float] = Field(..., description="Temperature range (min, max) in Celsius")
    max_precip: float = Field(..., description="Maximum precipitation in mm")
    max_wind: float = Field(..., description="Maximum wind speed in m/s")
    max_humidity: float = Field(..., description="Maximum humidity percentage")
    max_clouds: float = Field(..., description="Maximum cloud cover percentage")


class EventCriteriaResponse(BaseModel):
    """Response model for event criteria"""
    event: str = Field(..., description="Event name")
    criteria: Optional[EventCriteria] = Field(..., description="Event criteria")


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
from datetime import datetime
from typing import Dict, List

from weather_service import WeatherPlannerService
from models import (
    WeatherPlanningRequest, 
    WeatherPlanningResponse, 
    WeatherDay,
    AvailableOptionsResponse,
    EventCriteriaResponse,
    EventCriteria,
    ErrorResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="TzApp Weather Planning API",
    description="API pentru planificarea evenimentelor în funcție de vreme",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Alternative frontend ports
        "http://127.0.0.1:8080",
        "*"  # Allow all origins for development - remove in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize weather service
try:
    weather_service = WeatherPlannerService()
except FileNotFoundError as e:
    print(f"Warning: {e}")
    weather_service = None


@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "TzApp Weather Planning API", 
        "version": "1.0.0",
        "endpoints": [
            "/plan-event",
            "/available-options", 
            "/event-criteria/{event}"
        ]
    }


@app.post("/plan-event", response_model=WeatherPlanningResponse, tags=["Weather Planning"])
async def plan_event(request: WeatherPlanningRequest):
    """
    Găsește cele mai bune zile pentru un eveniment într-o anumită lună
    """
    if weather_service is None:
        raise HTTPException(status_code=500, detail="Weather service not available - data file not found")
    
    try:
        # Get best days from weather service
        best_days_df = weather_service.find_best_days(
            city=request.city,
            event=request.event,
            month=request.month,
            year=request.year,
            limit=request.limit
        )
        
        if best_days_df.empty:
            return WeatherPlanningResponse(
                success=True,
                city=request.city,
                event=request.event,
                month=request.month,
                year=request.year,
                best_days=[],
                message="Nu s-au găsit date pentru această perioadă"
            )
        
        # Convert DataFrame to list of WeatherDay objects
        best_days = []
        for _, row in best_days_df.iterrows():
            weather_day = WeatherDay(
                date=row['date'].strftime('%Y-%m-%d'),
                score=round(row['score'], 2),
                temp_celsius=round(row['temp_celsius'], 1),
                precip=round(row['precip'], 2),
                wind_max_speed=round(row['wind_max_speed'], 2),
                humidity_afternoon=round(row['humidity_afternoon'], 1),
                cloud_cover_afternoon=round(row['cloud_cover_afternoon'], 1)
            )
            best_days.append(weather_day)
        
        return WeatherPlanningResponse(
            success=True,
            city=request.city,
            event=request.event,
            month=request.month,
            year=request.year,
            best_days=best_days,
            message=f"Găsite {len(best_days)} zile potrivite pentru {request.event} în {request.city}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare internă: {str(e)}")


@app.get("/available-options", response_model=AvailableOptionsResponse, tags=["Configuration"])
async def get_available_options():
    """
    Obține lista de orașe și evenimente disponibile
    """
    if weather_service is None:
        raise HTTPException(status_code=500, detail="Weather service not available")
    
    return AvailableOptionsResponse(
        cities=weather_service.get_available_cities(),
        events=weather_service.get_available_events()
    )


@app.get("/event-criteria/{event}", response_model=EventCriteriaResponse, tags=["Configuration"])
async def get_event_criteria(event: str):
    """
    Obține criteriile pentru un anumit tip de eveniment
    """
    if weather_service is None:
        raise HTTPException(status_code=500, detail="Weather service not available")
    
    criteria_dict = weather_service.get_event_criteria(event.lower())
    
    if criteria_dict is None:
        available_events = weather_service.get_available_events()
        raise HTTPException(
            status_code=404, 
            detail=f"Evenimentul '{event}' nu există. Evenimente disponibile: {', '.join(available_events)}"
        )
    
    # Convert tuple to proper format for response
    criteria = EventCriteria(
        temp_range=criteria_dict['temp_range'],
        max_precip=criteria_dict['max_precip'],
        max_wind=criteria_dict['max_wind'],
        max_humidity=criteria_dict['max_humidity'],
        max_clouds=criteria_dict['max_clouds']
    )
    
    return EventCriteriaResponse(
        event=event.lower(),
        criteria=criteria
    )


@app.get("/health", tags=["General"])
async def health_check():
    """
    Health check endpoint
    """
    service_status = "available" if weather_service is not None else "unavailable"
    return {
        "status": "healthy",
        "weather_service": service_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
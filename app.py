from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
from datetime import datetime
from typing import Dict, List

from weather_service import WeatherPlannerService
from weather_script import WeatherModel, WeatherData
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"
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

# Initialize ML weather model
try:
    weather_model = WeatherModel()
    print("Weather ML model loaded successfully!")
except Exception as e:
    print(f"Warning: Could not load weather ML model: {e}")
    weather_model = None


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
                cloud_cover_afternoon=round(row['cloud_cover_afternoon'], 1),
                weather_category=row['weather_category']
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


@app.post("/categorize-weather", tags=["Weather Analysis"])
async def categorize_weather(weather_data: WeatherData):
    """
    Categorizează vremea pe baza datelor meteorologice folosind logica de categorii
    """
    try:
        # Use rule-based categorization instead of broken ML model
        temp = weather_data.temperature
        precip = weather_data.precipitation
        
        # Apply categorization logic in correct priority order
        if (temp <= 0) and (precip > 0.001):
            prediction = "snow"
        elif precip >= 0.03:
            prediction = "heavy_rain"
        elif (precip >= 0.005) and (precip < 0.03):
            prediction = "light_rain"
        elif temp >= 20:
            prediction = "hot"
        elif (temp < 10) and (precip < 0.005):
            prediction = "cold"
        elif (temp >= 10) and (temp < 20) and (precip < 0.005):
            prediction = "sunny"
        else:
            prediction = "sunny"  # default
        
        return {
            "success": True,
            "weather_category": prediction,
            "input_data": weather_data.model_dump(),
            "message": f"Vremea a fost categorizată ca: {prediction}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la categorizarea vremii: {str(e)}")


@app.post("/debug-categories", tags=["Debug"])
async def debug_categories(weather_data: WeatherData):
    """
    Debug endpoint to see category logic
    """
    if weather_model is None:
        raise HTTPException(status_code=500, detail="Model ML indisponibil")
    
    # Test category logic manually
    temp = weather_data.temperature
    precip = weather_data.precipitation
    
    # Test conditions from weather_script.py
    conditions = {
        'snow': (temp <= 0) and (precip > 0.001),
        'heavy_rain': precip >= 0.03,
        'light_rain': (precip >= 0.005) and (precip < 0.03),
        'hot': temp >= 20,
        'cold': (temp < 10) and (precip < 0.005),
        'sunny': (temp >= 10) and (temp < 20) and (precip < 0.005)
    }
    
    # Get ML prediction
    ml_prediction = weather_model.predict_weather_optimized(
        temperature=weather_data.temperature,
        precipitation=weather_data.precipitation,
        wind=weather_data.wind,
        relative_humidity=weather_data.relative_humidity,
        altitude=weather_data.altitude,
        air_pressure=weather_data.air_pressure
    )
    
    return {
        "input": weather_data.dict(),
        "category_conditions": conditions,
        "ml_prediction": ml_prediction,
        "expected_by_logic": next((k for k, v in conditions.items() if v), 'sunny')
    }

@app.get("/health", tags=["General"])
async def health_check():
    """
    Health check endpoint
    """
    service_status = "available" if weather_service is not None else "unavailable"
    model_status = "available" if weather_model is not None else "unavailable"
    return {
        "status": "healthy",
        "weather_service": service_status,
        "ml_model": model_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
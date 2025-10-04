import pandas as pd
from datetime import datetime
import numpy as np
from typing import Dict, Tuple, List, Optional
import os

# Try to import weather model, but don't fail if it's not available
try:
    from weather_script import WeatherModel
    ML_MODEL_AVAILABLE = True
except ImportError:
    ML_MODEL_AVAILABLE = False
    print("Warning: WeatherModel not available, will use default categorization")


CITY_COORDINATES = {
    'Alba': (46.06667, 23.58333),
    'Arad': (46.16667, 21.31667),
    'Bacau': (46.56667, 26.91667),
    'Baia Mare': (47.65969, 23.56808),
    'Bistrita': (47.13316, 24.50069),
    'Brasov': (45.64861, 25.60613),
    'Bucuresti': (44.43225, 26.10626),
    'Buzau': (45.14802, 26.82148),
    'Cluj': (46.76667, 23.6),
    'Constanta': (44.18073, 28.63432),
    'Craiova': (44.31667, 23.8),
    'Deva': (45.88333, 22.9),
    'Drobeta-Turnu Severin': (44.63188, 22.65648),
    'Galati': (45.45, 28.03333),
    'Iasi': (47.16667, 27.6),
    'Oradea': (47.06667, 21.93333),
    'Petrosani': (45.41667, 23.36667),
    'Pitesti': (44.85, 24.86667),
    'Ramnicu Valcea': (45.1, 24.36667),
    'Satu Mare': (47.8, 22.88333),
    'Sibiu': (45.8, 24.15),
    'Slobozia': (44.56667, 27.36667),
    'Suceava': (47.63333, 26.25),
    'Timisoara': (45.75372, 21.22571)
}


EVENT_CRITERIA = {
    'picnic': {
        'temp_range': (18, 26),
        'max_precip': 0.5,
        'max_wind': 4.0,
        'max_humidity': 70,
        'max_clouds': 60
    },
    'festival': {
        'temp_range': (15, 28),
        'max_precip': 1.0,
        'max_wind': 6.0,
        'max_humidity': 75,
        'max_clouds': 80
    },
    'pool_party': {
        'temp_range': (22, 32),
        'max_precip': 0.0,
        'max_wind': 3.0,
        'max_humidity': 65,
        'max_clouds': 40
    },
    'concert': {
        'temp_range': (12, 25),
        'max_precip': 0.2,
        'max_wind': 5.0,
        'max_humidity': 80,
        'max_clouds': 70
    },
    'drumetie': {
        'temp_range': (8, 22),
        'max_precip': 0.1,
        'max_wind': 7.0,
        'max_humidity': 80,
        'max_clouds': 70
    },
    'nunta': {
        'temp_range': (16, 26),
        'max_precip': 0.0,
        'max_wind': 3.0,
        'max_humidity': 65,
        'max_clouds': 30
    },
    'zi_nastere': {
        'temp_range': (15, 27),
        'max_precip': 0.3,
        'max_wind': 4.0,
        'max_humidity': 75,
        'max_clouds': 60
    }
}


class WeatherPlannerService:
    def __init__(self, csv_file_path: str = "../SmartPlanner/weather_data.csv"):
        """Initialize the weather planner service with the CSV file path"""
        self.csv_file_path = csv_file_path
        if not os.path.exists(csv_file_path):
            # Try alternative path
            alternative_path = "SmartPlanner/weather_data.csv"
            if os.path.exists(alternative_path):
                self.csv_file_path = alternative_path
            else:
                raise FileNotFoundError(f"Weather data file not found at {csv_file_path}")
        
        # Initialize ML model if available
        self.ml_model = None
        if ML_MODEL_AVAILABLE:
            try:
                self.ml_model = WeatherModel()
                print("ML Weather model loaded successfully in WeatherPlannerService!")
            except Exception as e:
                print(f"Could not load ML model: {e}")
                self.ml_model = None
    
    @staticmethod
    def kelvin_to_celsius(temp_k: float) -> float:
        """Convert temperature from Kelvin to Celsius"""
        return temp_k - 273.15

    @staticmethod
    def calculate_event_score(row: pd.Series, criteria: Dict) -> float:
        """Calculate score for a day based on event criteria"""
        score = 0
        
        temp_c = WeatherPlannerService.kelvin_to_celsius(row['afternoon_temp'])
        
        temp_min, temp_max = criteria['temp_range']
        if temp_min <= temp_c <= temp_max:
            score += 30
        else:
            temp_penalty = min(abs(temp_c - temp_min), abs(temp_c - temp_max))
            score += max(0, 30 - temp_penalty * 2)
        
        if row['precip'] <= criteria['max_precip']:
            score += 25
        else:
            score += max(0, 25 - (row['precip'] - criteria['max_precip']) * 10)
        
        if row['wind_max_speed'] <= criteria['max_wind']:
            score += 20
        else:
            score += max(0, 20 - (row['wind_max_speed'] - criteria['max_wind']) * 3)
        
        if row['humidity_afternoon'] <= criteria['max_humidity']:
            score += 15
        else:
            score += max(0, 15 - (row['humidity_afternoon'] - criteria['max_humidity']) * 0.3)
        
        if row['cloud_cover_afternoon'] <= criteria['max_clouds']:
            score += 10
        else:
            score += max(0, 10 - (row['cloud_cover_afternoon'] - criteria['max_clouds']) * 0.2)
        
        return round(score, 2)

    def find_best_days(self, city: str, event: str, month: int, year: int = 2025, limit: int = 5) -> pd.DataFrame:
        """
        Find the best days for an event in a specific month
        
        Args:
            city: city name
            event: event type
            month: month (1-12)
            year: year (default 2025)
            limit: number of best days to return (default 5)
        
        Returns:
            DataFrame with the best days sorted by score
        """
        
        if city not in CITY_COORDINATES:
            available_cities = ", ".join(CITY_COORDINATES.keys())
            raise ValueError(f"City '{city}' not available. Available cities: {available_cities}")

        if event not in EVENT_CRITERIA:
            available_events = ", ".join(EVENT_CRITERIA.keys())
            raise ValueError(f"Event '{event}' not available. Available events: {available_events}")
        
        df = pd.read_csv(self.csv_file_path)
        df['date'] = pd.to_datetime(df['date'])
        
        city_lat, city_lon = CITY_COORDINATES[city]
        city_data = df[(df['lat'] == city_lat) & (df['lon'] == city_lon)].copy()
        
        month_data = city_data[
            (city_data['date'].dt.month == month) &
            (city_data['date'].dt.year == year)
        ].copy()
        
        if month_data.empty:
            return pd.DataFrame()

        criteria = EVENT_CRITERIA[event]
        month_data['score'] = month_data.apply(
            lambda row: self.calculate_event_score(row, criteria), axis=1
        )
        
        best_days = month_data.nlargest(limit, 'score')[
            ['date', 'score', 'afternoon_temp', 'precip', 'wind_max_speed', 
             'humidity_afternoon', 'cloud_cover_afternoon']
        ].copy()
        
        best_days['temp_celsius'] = best_days['afternoon_temp'].apply(self.kelvin_to_celsius)
        
        # Add weather categorization using ML model
        best_days['weather_category'] = best_days.apply(self.categorize_weather_ml, axis=1)
        
        return best_days

    def get_available_cities(self) -> List[str]:
        """Get list of available cities"""
        return list(CITY_COORDINATES.keys())

    def get_available_events(self) -> List[str]:
        """Get list of available events"""
        return list(EVENT_CRITERIA.keys())

    def get_event_criteria(self, event: str) -> Optional[Dict]:
        """Get criteria for a specific event"""
        return EVENT_CRITERIA.get(event)

    def categorize_weather_ml(self, row: pd.Series) -> str:
        """
        Categorize weather using ML model based on weather data
        Falls back to simple categorization if ML model is not available
        """
        if self.ml_model is not None:
            try:
                # Convert temperature from Kelvin to Celsius for ML model
                temp_celsius = self.kelvin_to_celsius(row['afternoon_temp'])
                
                # Extract weather parameters (using default values if missing)
                precipitation = row.get('precip', 0.0)
                wind = row.get('wind_max_speed', 0.0)
                humidity = row.get('humidity_afternoon', 50.0)
                
                # Use default values for missing data
                altitude = 100.0  # Default altitude
                air_pressure = 1013.25  # Standard air pressure
                
                # Get ML prediction
                category = self.ml_model.predict_weather_optimized(
                    temperature=temp_celsius,
                    precipitation=precipitation,
                    wind=wind,
                    relative_humidity=humidity,
                    altitude=altitude,
                    air_pressure=air_pressure
                )
                
                return category
                
            except Exception as e:
                print(f"ML categorization failed: {e}, using fallback")
                return self._fallback_categorization(row)
        else:
            return self._fallback_categorization(row)
    
    def _fallback_categorization(self, row: pd.Series) -> str:
        """
        Simple weather categorization when ML model is not available
        """
        temp_celsius = self.kelvin_to_celsius(row['afternoon_temp'])
        precipitation = row.get('precip', 0.0)
        
        # Simple rules for weather categorization
        if temp_celsius <= 0 and precipitation > 0.001:
            return "snow"
        elif precipitation >= 0.03:
            return "heavy_rain"
        elif precipitation >= 0.005:
            return "light_rain"
        elif temp_celsius >= 20:
            return "hot"
        elif temp_celsius < 10:
            return "cold"
        else:
            return "sunny"
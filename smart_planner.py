import pandas as pd
from datetime import datetime
import numpy as np


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

def kelvin_to_celsius(temp_k):
    """Convertește temperatura din Kelvin în Celsius"""
    return temp_k - 273.15

def calculate_event_score(row, criteria):
    """Calculează scorul pentru o zi bazat pe criteriile evenimentului"""
    score = 0
    
    # Convertește temperatura din Kelvin în Celsius
    temp_c = kelvin_to_celsius(row['afternoon_temp'])
    
    # Scor pentru temperatură (0-30 puncte)
    temp_min, temp_max = criteria['temp_range']
    if temp_min <= temp_c <= temp_max:
        score += 30
    else:
        temp_penalty = min(abs(temp_c - temp_min), abs(temp_c - temp_max))
        score += max(0, 30 - temp_penalty * 2)
    
    # Scor pentru precipitații (0-25 puncte)
    if row['precip'] <= criteria['max_precip']:
        score += 25
    else:
        score += max(0, 25 - (row['precip'] - criteria['max_precip']) * 10)
    
    # Scor pentru vânt (0-20 puncte)
    if row['wind_max_speed'] <= criteria['max_wind']:
        score += 20
    else:
        score += max(0, 20 - (row['wind_max_speed'] - criteria['max_wind']) * 3)
    
    # Scor pentru umiditate (0-15 puncte)
    if row['humidity_afternoon'] <= criteria['max_humidity']:
        score += 15
    else:
        score += max(0, 15 - (row['humidity_afternoon'] - criteria['max_humidity']) * 0.3)
    
    # Scor pentru înnorare (0-10 puncte)
    if row['cloud_cover_afternoon'] <= criteria['max_clouds']:
        score += 10
    else:
        score += max(0, 10 - (row['cloud_cover_afternoon'] - criteria['max_clouds']) * 0.2)
    
    return round(score, 2)

def find_best_days(csv_file, city, event, month, year=2025):
    """
    Găsește cele mai bune 5 zile pentru un eveniment într-o anumită lună
    
    Args:
        csv_file: calea către fișierul CSV
        city: numele orașului
        event: tipul evenimentului
        month: luna (1-12)
        year: anul (default 2025)
    
    Returns:
        DataFrame cu cele mai bune 5 zile sortate după scor
    """
    
    if city not in CITY_COORDINATES:
        raise ValueError(f"Orașul {city} nu este în lista disponibilă")

    if event not in EVENT_CRITERIA:
        raise ValueError(f"Evenimentul {event} nu este în lista disponibilă")
    
    df = pd.read_csv(csv_file)
    
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
        lambda row: calculate_event_score(row, criteria), axis=1
    )
    
    best_days = month_data.nlargest(5, 'score')[
        ['date', 'score', 'afternoon_temp', 'precip', 'wind_max_speed', 
         'humidity_afternoon', 'cloud_cover_afternoon']
    ].copy()
    
    best_days['temp_celsius'] = best_days['afternoon_temp'].apply(kelvin_to_celsius)
    
    return best_days

def main():
    """Funcția principală pentru testare"""
    

    print("=== SMART PLANNER ===\n")
    

    print("Orașe disponibile:", list(CITY_COORDINATES.keys()))
    print("Evenimente disponibile:", list(EVENT_CRITERIA.keys()))
    print()
    
    try:
        city = "Craiova"
        event = "picnic" 
        month = 5
        year = 2026
        
        print(f"Căutare: {event} în {city}, luna {month}/{year}")
        print("-" * 50)
        
        best_days = find_best_days('weather_data.csv', city, event, month, year)
        
        if not best_days.empty:
            print("Cele mai bune 5 zile:")
            for idx, row in best_days.iterrows():
                print(f"{row['date'].strftime('%Y-%m-%d')} - Scor: {row['score']}/100")
                print(f"  Temp: {row['temp_celsius']:.1f}°C, Precipitații: {row['precip']:.1f}mm")
                print(f"  Vânt: {row['wind_max_speed']:.1f}m/s, Umiditate: {row['humidity_afternoon']:.0f}%")
                print(f"  Înnorare: {row['cloud_cover_afternoon']:.0f}%")
                print()
        else:
            print("Nu s-au găsit date pentru această perioadă")
            
    except Exception as e:
        print(f"Eroare: {e}")

if __name__ == "__main__":
    main()
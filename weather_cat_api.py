from fastapi import FastAPI
from weather_script import WeatherData, WeatherModel
import uvicorn

app = FastAPI()
model = WeatherModel()

@app.post('/predict')
def predict_weather(weather: WeatherData):
    data = weather.model_dump()
    prediction = model.predict_weather_optimized(
        data['temperature'], data['precipitation'], data['wind'],
        data['relative_humidity'], data['altitude'],
        data['air_pressure']
    )
    return {
        'prediction': prediction
    }

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
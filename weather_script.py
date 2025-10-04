import pandas as pd
import numpy as np
import seaborn as sns
from pydantic import BaseModel

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import joblib
from lightgbm import LGBMClassifier

class WeatherData(BaseModel):
	temperature: float
	precipitation: float
	wind: float
	relative_humidity: float
	altitude: float
	air_pressure: float

class WeatherModel:
	def __init__(self):
		self.weather_df = pd.read_csv("weather_daily_2021_2022.csv")
		self.model_fname_ = 'weather_categorization_model.pkl'
		self.weather_df.drop(columns=['latitude', 'longitude', 'date'], inplace=True, axis=1)
		try:
			saved_data = joblib.load(self.model_fname_)
			self.model = saved_data['model']
			self.label = saved_data['label_encoder']
		except Exception as _:
			self.weather_df = self.create_categories()
			self.weather_df = self.create_optimized_features()
			self.model = self.train_model()

	def create_categories(self):
		'''Define 6 categories for weather'''

		conditions = [
			# SNOW
			(self.weather_df['temperature'] <= 0) & (self.weather_df['precipitation'] > 0.001),
			# HEAVY_RAIN
			(self.weather_df['precipitation'] >= 0.03),

			# LIGHT_RAIN
			(self.weather_df['precipitation'] >= 0.005) & (self.weather_df['precipitation'] < 0.03),

			# HOT
			(self.weather_df['temperature'] >= 20),

			# COLD
			(self.weather_df['temperature'] < 10) & (self.weather_df['precipitation'] < 0.005),

			# SUNNY
			(self.weather_df['temperature'] >= 10) & (self.weather_df['temperature'] < 20) & (self.weather_df['precipitation'] < 0.005)
		]

		choices = ['snow', 'heavy_rain', 'light_rain', 'hot', 'cold', 'sunny']
		self.weather_df['weather_category'] = np.select(conditions, choices, default='sunny')

		return self.weather_df

	def create_optimized_features(self):
		self.weather_df['wind_chill'] = 13.12 + 0.6215*self.weather_df['temperature'] - 11.37*(self.weather_df['wind']**0.16) + 0.3965*self.weather_df['temperature']*(self.weather_df['wind']**0.16)
		self.weather_df['feels_like'] = self.weather_df['temperature'] + 0.3 * self.weather_df['relative_humidity'] - 0.7 * self.weather_df['wind']

		self.weather_df['precip_humidity_interaction'] = self.weather_df['precipitation'] * self.weather_df['relative_humidity']
		self.weather_df['temp_pressure_interaction'] = self.weather_df['temperature'] * (self.weather_df['air_pressure'] / 1000)

		self.weather_df['is_freezing'] = (self.weather_df['temperature'] <= 0).astype(int)
		self.weather_df['is_raining'] = (self.weather_df['precipitation'] > 0.005).astype(int)
		self.weather_df['is_windy'] = (self.weather_df['wind'] > 8).astype(int)
		self.weather_df['is_humid'] = (self.weather_df['relative_humidity'] > 2.0).astype(int)

		self.weather_df['is_high_altitude'] = (self.weather_df['altitude'] > 800).astype(int)

		return self.weather_df

	def train_model(self):
		self.optimal_features = [
			'temperature', 'precipitation', 'wind', 'relative_humidity', 'altitude', 'air_pressure',
			'feels_like', 'precip_humidity_interaction', 'temp_pressure_interaction',
			'is_freezing', 'is_raining', 'is_windy', 'is_humid', 'is_high_altitude'
		]

		self.label = LabelEncoder()
		self.weather_df['weather_encoded'] = self.label.fit_transform(self.weather_df['weather_category'])
		self.X = self.weather_df[self.optimal_features]
		self.y = self.weather_df['weather_encoded']
		X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42, stratify=self.y)

		model = LGBMClassifier(
			n_estimators=800,
			max_depth=7,
			learning_rate=0.1,
			subsample=0.7,
			colsample_bytree=0.7,
			reg_alpha=0.3,
			reg_lambda=0.3,
			random_state=42,
			class_weight='balanced',
			min_child_samples=25,
			min_split_gain=0.01,
			n_jobs=-1,
			objective='multiclass',
			boosting_type='gbdt',
			metric='multi_logloss'
		)

		model.fit(X_train, y_train, eval_set=[(X_test, y_test)], eval_metric='multi_logloss', callbacks=[
				lgb.early_stopping(50, verbose=0),   
				lgb.log_evaluation(100)        
			])

		y_pred_test = model.predict(X_test)
		joblib.dump({'model': model, 'label_encoder': self.label}, self.model_fname_)
		return model

	def predict_weather_optimized(self, temperature, precipitation, wind, relative_humidity, altitude, air_pressure):
		try:
			# Validare input
			if any(not isinstance(x, (int, float)) for x in [temperature, precipitation, wind, relative_humidity, altitude, air_pressure]):
				raise ValueError("Toate valorile trebuie să fie numere")
			if relative_humidity < 0 or relative_humidity > 100:
				raise ValueError("Umiditatea relativă trebuie să fie între 0 și 100%")
			if precipitation < 0:
				raise ValueError("Precipitațiile nu pot fi negative")
			if wind < 0:
				raise ValueError("Viteza vântului nu poate fi negativă")
			if air_pressure < 0:
				raise ValueError("Presiunea atmosferică nu poate fi negativă")

			# Calculează feature-urile derivate
			feels_like = temperature + 0.3 * relative_humidity - 0.7 * wind
			precip_humidity_interaction = precipitation * relative_humidity
			temp_pressure_interaction = temperature * (air_pressure / 1000)
			
			# Condiții binare
			is_freezing = 1 if temperature <= 0 else 0
			is_raining = 1 if precipitation > 0.005 else 0
			is_windy = 1 if wind > 8 else 0
			is_humid = 1 if relative_humidity > 2.0 else 0
			is_high_altitude = 1 if altitude > 800 else 0
			
			# Feature vector în ordinea corectă
			features = np.array([[temperature, precipitation, wind, relative_humidity, altitude, air_pressure,
				feels_like, precip_humidity_interaction, temp_pressure_interaction,
				is_freezing, is_raining, is_windy, is_humid, is_high_altitude
			]])
			
			# Predicție
			prediction_encoded = self.model.predict(features)[0]
			prediction = self.label.inverse_transform([prediction_encoded])[0]
			
			return prediction
		except Exception as e:
			print(f"Error in prediction: {e}")
			raise

# model = WeatherModel()
# prediction = model.predict_weather_optimized(
#     temperature=20.5,
#     precipitation=0.5,
#     wind=3.2,
#     relative_humidity=65.0,
#     altitude=100.0,
#     air_pressure=1013.25
# )

# print(f"Predicted weather category: {prediction}")

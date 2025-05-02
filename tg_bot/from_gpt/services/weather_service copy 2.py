import requests
from datetime import datetime, timedelta
import os

# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_API_KEY = ''
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_weather_forecast(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    timestamps = []
    temps = []
    wind_speeds = []
    wind_gusts = []
    precipitation = []
    conditions = []

    now = datetime.utcnow()
    limit = now + timedelta(days=2)

    for entry in data.get("list", []):
        dt = datetime.utcfromtimestamp(entry["dt"])
        if dt > limit:
            continue

        timestamps.append(dt)
        temps.append(entry["main"]["temp"])
        wind_speeds.append(entry["wind"].get("speed", 0))
        wind_gusts.append(entry["wind"].get("gust", 0))

        # осадки: берем max из rain или snow
        rain = entry.get("rain", {}).get("3h", 0)
        snow = entry.get("snow", {}).get("3h", 0)
        precipitation.append(max(rain, snow))

        # погодные условия
        condition = entry["weather"][0]["description"]
        conditions.append(condition)

    return {
        "timestamps": timestamps,
        "temps": temps,
        "wind_speeds": wind_speeds,
        "wind_gusts": wind_gusts,
        "precipitation": precipitation,
        "conditions": conditions
    }

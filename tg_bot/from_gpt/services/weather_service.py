import requests
from datetime import datetime, timedelta
from io import BytesIO
from utils.plot_utils import (
    plot_temperature,
    plot_wind,
    plot_precipitation,
    plot_conditions,
)

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
        rain = entry.get("rain", {}).get("3h", 0)
        snow = entry.get("snow", {}).get("3h", 0)
        precipitation.append(max(rain, snow))
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

def get_weather_forecast_and_plots(lat, lon):
    data = get_weather_forecast(lat, lon)
    plots = [
        plot_temperature(data['timestamps'], data['temps']),
        plot_wind(data['timestamps'], data['wind_speeds'], data['wind_gusts']),
        plot_precipitation(data['timestamps'], data['precipitation']),
        plot_conditions(data['timestamps'], data['conditions']),
    ]
    return plots

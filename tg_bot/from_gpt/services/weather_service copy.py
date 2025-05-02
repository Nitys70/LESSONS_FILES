import requests
import os
from datetime import datetime

# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "вставь_сюда_свой_ключ")
OPENWEATHER_API_KEY = ''
# Получаем прогноз погоды по координатам
def get_weather_forecast(coords):
    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "exclude": "minutely,current,daily,alerts",
        "lang": "ru"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Возвращаем только ближайшие 48 часов
    return data.get("hourly", [])[:48]

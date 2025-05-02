import requests
import os

# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "вставь_сюда_свой_ключ")
OPENWEATHER_API_KEY = ''
# Получаем координаты по названию города
def get_coordinates(city_name: str):
    url = f"http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city_name,
        "limit": 1,
        "appid": OPENWEATHER_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200 and data:
        return {
            "lat": data[0]["lat"],
            "lon": data[0]["lon"]
        }
    return None

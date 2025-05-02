import re
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="weather_bot")

def get_coordinates_by_name(location_name: str):
    try:
        location = geolocator.geocode(location_name, language='ru')
        if location:
            coords = (location.latitude, location.longitude)
            display_name = location.address
            return coords, display_name
        return None, None
    except Exception as e:
        print(f"Ошибка геокодера: {e}")
        return None, None

def parse_custom_location(text: str):
    try:
        match = re.match(r"(.+?)\s+([\d\.]+)\s+([\d\.]+)", text)
        if match:
            name = match.group(1).strip()
            lat = float(match.group(2))
            lon = float(match.group(3))
            return name, lat, lon
    except:
        pass
    return None

def format_location(name: str, lat: float, lon: float):
    return f"{name} ({lat}, {lon})"

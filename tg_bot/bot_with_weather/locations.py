import pickle
import os
from typing import Dict, Tuple

def get_user_file(user_id: int) -> str:
    return f"data/user_{user_id}_locations.pkl"

def load_locations(user_id: int) -> Dict[str, Tuple[float, float]]:
    """Загружает локации пользователя"""
    os.makedirs("data", exist_ok=True)
    try:
        with open(get_user_file(user_id), "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return {}

def save_location(user_id: int, name: str, lat: float, lon: float):
    """Сохраняет новую локацию"""
    locations = load_locations(user_id)
    locations[name.lower()] = (lat, lon)
    with open(get_user_file(user_id), "wb") as f:
        pickle.dump(locations, f)

def delete_location(user_id: int, name: str):
    """Удаляет локацию"""
    locations = load_locations(user_id)
    if name.lower() in locations:
        del locations[name.lower()]
        with open(get_user_file(user_id), "wb") as f:
            pickle.dump(locations, f)
        return True
    return False
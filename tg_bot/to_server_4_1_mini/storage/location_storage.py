import os
import pickle

STORAGE_PATH = "storage/location_data.pkl"

def load_all_locations():
    if os.path.exists(STORAGE_PATH):
        with open(STORAGE_PATH, "rb") as f:
            return pickle.load(f)
    return {}

def save_all_locations(data):
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    with open(STORAGE_PATH, "wb") as f:
        pickle.dump(data, f)

def save_location(user_id, name, lat, lon):
    data = load_all_locations()
    user_data = data.get(user_id, {})
    user_data[name.lower()] = {"name": name, "lat": lat, "lon": lon}
    data[user_id] = user_data
    save_all_locations(data)

def load_location(user_id, name=None):
    data = load_all_locations()
    user_data = data.get(user_id)
    if not user_data:
        return None

    if name:
        return user_data.get(name.lower())
    else:
        # Если имя не указано, вернуть последнюю сохраненную локацию
        return next(reversed(user_data.values())) if user_data else None

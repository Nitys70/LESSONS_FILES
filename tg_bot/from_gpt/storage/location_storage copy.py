import os
import pickle

STORAGE_PATH = "data/locations.pkl"

# Убедимся, что директория существует
os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)

# Загрузить все сохранённые локации
def load_locations():
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, "rb") as f:
        return pickle.load(f)

# Сохранить все локации
def save_locations(locations):
    with open(STORAGE_PATH, "wb") as f:
        pickle.dump(locations, f)

# Сохранить локацию конкретного пользователя
def save_user_location(user_id, coords):
    locations = load_locations()
    locations[user_id] = coords
    save_locations(locations)

# Получить сохранённую локацию пользователя
def get_user_location(user_id):
    locations = load_locations()
    return locations.get(user_id)

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import pickle
import os

from services import location_service, weather_service
from utils import plot_utils

# Состояния диалога
CHOOSE_LOCATION, CONFIRM_SAVE = range(2)

# Файл с локациями
LOCATION_FILE = "data/locations.pkl"


def load_locations():
    if os.path.exists(LOCATION_FILE):
        with open(LOCATION_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def save_locations(locations):
    with open(LOCATION_FILE, "wb") as f:
        pickle.dump(locations, f)


# 1. Старт диалога
async def start_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название интересующего вас города:")
    return CHOOSE_LOCATION


# 2. Пользователь вводит город
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    coords = location_service.get_coordinates(city)

    if coords is None:
        await update.message.reply_text("Не удалось найти город. Попробуйте снова.")
        return CHOOSE_LOCATION

    # Сохраняем временно, пока не подтвердят
    context.user_data['pending_location'] = {
        'city': city,
        'coords': coords,
    }

    await update.message.reply_text(
        f"Город '{city}' найден.\nСохранить эту локацию на будущее? (Да / Нет)"
    )
    return CONFIRM_SAVE


# 3. Пользователь подтверждает или отказывается
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    user_id = update.effective_user.id
    pending = context.user_data.get('pending_location')

    if not pending:
        await update.message.reply_text("Что-то пошло не так. Попробуйте снова.")
        return ConversationHandler.END

    if answer in ["да", "yes", "y", "д"]:
        locations = load_locations()
        locations[user_id] = pending['coords']
        save_locations(locations)
        await update.message.reply_text("Локация сохранена ✅")
    else:
        await update.message.reply_text("Хорошо, локация не будет сохранена.")

    # Показываем прогноз
    forecast = weather_service.get_weather_forecast(pending['coords'])
    image_path = plot_utils.plot_forecast(forecast)

    with open(image_path, "rb") as img:
        await update.message.reply_photo(img, caption=f"Прогноз погоды для {pending['city']}:")

    context.user_data.pop('pending_location', None)
    return ConversationHandler.END


# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, отмена.")
    return ConversationHandler.END

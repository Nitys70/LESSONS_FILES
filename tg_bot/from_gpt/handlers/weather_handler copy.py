from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from services import location_service, weather_service
from utils import plot_utils
from storage.location_storage import save_user_location

# Состояния FSM
ASK_LOCATION, CONFIRM_SAVE = range(2)

# Запуск сценария по слову "погода"
async def handle_weather_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🌍 Введите интересующую вас локацию (например: Москва, Санкт-Петербург, Нью-Йорк):"
    )
    return ASK_LOCATION

# Получение локации от пользователя и попытка найти координаты
async def process_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text.strip()
    coords = location_service.get_coordinates(city)

    if not coords:
        await update.message.reply_text(
            "❌ Не удалось найти локацию. Убедитесь, что вы ввели корректное название города."
        )
        return ASK_LOCATION

    context.user_data["pending_location"] = {
        "city": city,
        "coords": coords,
    }

    await update.message.reply_text(
        f"📍 Найдено: {city}\nШирота: {coords['lat']}, Долгота: {coords['lon']}\n\n"
        "Сохранить эту локацию на будущее? (да/нет)"
    )
    return CONFIRM_SAVE

# Подтверждение сохранения и показ прогнозов
async def confirm_save_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    pending = context.user_data.get("pending_location")

    if not pending:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

    if text in ("да", "сохранить", "ага", "ок"):
        save_user_location(update.effective_user.id, pending['coords'])
        await update.message.reply_text("✅ Локация сохранена.")
    else:
        await update.message.reply_text("🗺️ Локация не сохранена, используется только сейчас.")

    await update.message.reply_text("⏳ Получаю прогноз и генерирую графики...")

    forecast = weather_service.get_weather_forecast(pending['coords'])

    # Генерируем и отправляем графики
    for plot_func in [
        plot_utils.plot_forecast,
        plot_utils.plot_wind,
        plot_utils.plot_precipitation,
        plot_utils.plot_weather_description,
    ]:
        try:
            image_path = plot_func(forecast)
            with open(image_path, "rb") as img:
                await update.message.reply_photo(img)
        except Exception as e:
            print(f"Ошибка при генерации графика: {e}")

    await update.message.reply_text("📡 Прогноз погоды предоставлен. Можете продолжать общение с ботом.")
    return ConversationHandler.END

# Отмена сценария
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ConversationHandler для погоды
weather_conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(погода|Погода)$"), handle_weather_request)],
    states={
        ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_location)],
        CONFIRM_SAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_save_location)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

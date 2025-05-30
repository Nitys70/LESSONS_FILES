from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from services.location_service import get_coordinates_by_name, parse_custom_location, format_location

from services.weather_service import get_weather_forecast_and_plots

from storage.location_storage import load_location, save_location

ASK_LOCATION, CONFIRM_LOCATION, ASK_SAVE_LOCATION, MANUAL_LOCATION_INPUT = range(4)

async def handle_weather_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, введите название населённого пункта, который вас интересует:")
    return ASK_LOCATION

async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    location_name = update.message.text.strip()
    context.user_data['location_name'] = location_name

    # Проверяем, есть ли сохранённая локация для этого имени
    saved = load_location(user_id)
    if saved and saved['name'].lower() == location_name.lower():
        lat, lon = saved['lat'], saved['lon']
        context.user_data['coords'] = (lat, lon)
        await update.message.reply_text(
            f"Вы имеете в виду {saved['name']} ({lat}, {lon})? (да/нет)"
        )
        return CONFIRM_LOCATION

    # Пытаемся получить координаты через API
    coords, display_name = get_coordinates_by_name(location_name)
    if coords:
        context.user_data['coords'] = coords
        context.user_data['display_name'] = display_name
        await update.message.reply_text(
            f"Вас интересует погода в этой локации: {display_name} ({coords[0]}, {coords[1]})? (да/нет)"
        )
        return CONFIRM_LOCATION
    else:
        await update.message.reply_text("Не удалось определить координаты. Пожалуйста, введите вручную в формате: Название 56.17 47.36")
        return MANUAL_LOCATION_INPUT

async def confirm_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "да":
        return await send_weather(update, context)
    else:
        await update.message.reply_text("Хорошо, введите вручную в формате: Название 56.17 47.36")
        return MANUAL_LOCATION_INPUT

async def manual_location_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    parsed = parse_custom_location(text)
    if parsed:
        name, lat, lon = parsed
        context.user_data['coords'] = (lat, lon)
        context.user_data['location_name'] = name
        context.user_data['display_name'] = f"{name} ({lat}, {lon})"
        await update.message.reply_text("Сохранить эту локацию на будущее? (да/нет)")
        return ASK_SAVE_LOCATION
    else:
        await update.message.reply_text("Неверный формат. Пожалуйста, введите в формате: Название 56.17 47.36")
        return MANUAL_LOCATION_INPUT

async def ask_save_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text.lower()
    if answer == "да":
        lat, lon = context.user_data['coords']
        name = context.user_data['location_name']
        save_location(user_id, name, lat, lon)
    return await send_weather(update, context)

async def send_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coords = context.user_data['coords']
    display_name = context.user_data.get('display_name', '')

    await update.message.reply_text("Запрашиваю прогноз погоды...")

    try:
        plots = get_weather_forecast_and_plots(coords[0], coords[1])
        for plot in plots:
            await update.message.reply_photo(photo=plot)

        await update.message.reply_text("Если хотите узнать погоду для другого города, просто напишите 'погода'.")
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при получении прогноза погоды.")
        print("❌ Ошибка:", e)

    return ConversationHandler.END

weather_conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("(?i)^погода$"), handle_weather_request)],
    states={
        ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location)],
        CONFIRM_LOCATION: [MessageHandler(filters.Regex("(?i)^(да|нет)$"), confirm_location)],
        MANUAL_LOCATION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_location_input)],
        ASK_SAVE_LOCATION: [MessageHandler(filters.Regex("(?i)^(да|нет)$"), ask_save_location)],
    },
    fallbacks=[],
)

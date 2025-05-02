TELEGRAM_TOKEN = ""
OPENAI_API_KEY = ""
WEATHER_API_KEY = ""
AUTH_PASSWORD = ""

import openai
import os
import requests
from datetime import datetime
import logging
import json
import pickle
import traceback

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'  # Логи будут сохраняться в файл
)
logger = logging.getLogger(__name__)

# Константы для состояний ConversationHandler
WEATHER_CITY, LOCATION_NAME, DELETE_LOCATION = range(3)

# Токены (замените на свои)
# TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"
# OPENAI_API_KEY = "YOUR_OPENAI_KEY"
# WEATHER_API_KEY = "YOUR_WEATHER_API_KEY"
# AUTH_PASSWORD = "1206"

# Глобальные переменные для логирования
user_logins = set()
current_date = datetime.now().date()
user_links = set()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает все необработанные исключения."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    
    error_message = (
        f"An exception was raised while handling an update\n"
        f"update = {update}\n"
        f"context.chat_data = {context.chat_data}\n"
        f"context.user_data = {context.user_data}\n"
        f"traceback:\n{tb_string}"
    )
    
    logger.error(error_message)
    
    if isinstance(update, Update):
        try:
            await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        except:
            try:
                await update.callback_query.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            except:
                pass

async def log_user(update: Update):
    """Логирует уникальных пользователей"""
    global current_date, user_logins
    
    today = datetime.now().date()
    if today != current_date:
        user_logins.clear()
        current_date = today
    
    user_id = update.effective_user.id
    user_link = f"@{update.effective_user.username}" if update.effective_user.username else str(user_id)
    
    if user_id not in user_logins:
        user_logins.add(user_id)
        user_links.add(user_link)
        logger.info(f"New user: {user_id} ({user_link})")
        
        with open('daily_users.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {user_id} | {user_link}\n")

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет авторизацию пользователя"""
    try:
        return context.user_data.get('authorized', False)
    except Exception as e:
        logger.error(f"Error in check_auth: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        await log_user(update)
        
        if not await check_auth(update, context):
            await update.message.reply_text(
                "🔒 Для использования бота введите пароль.\n"
                "Если у вас нет пароля, обратитесь к администратору."
            )
            return
        
        await show_main_menu(update)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await error_handler(update, context)

async def show_main_menu(update: Update):
    """Показывает главное меню"""
    try:
        keyboard = [
            ["💬 Чат с GPT", "🌤️ Прогноз погоды"],
            ["⭐ Мои локации", "⚙️ Помощь"]
        ]
        await update.message.reply_text(
            "Добро пожаловать! Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Error in show_main_menu: {e}")
        raise

# ... (остальные функции остаются такими же, как в предыдущем примере, 
# но каждая должна быть обернута в try-except блок)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик текстовых сообщений"""
    try:
        await log_user(update)
        
        # Проверка авторизации
        if not await check_auth(update, context):
            if update.message.text == AUTH_PASSWORD:
                context.user_data['authorized'] = True
                await show_main_menu(update)
                return
            else:
                await update.message.reply_text("❌ Неверный пароль. Попробуйте ещё раз.")
                return

        text = update.message.text
        
        # Обработка команд главного меню
        if text == "🌤️ Прогноз погоды":
            await weather_menu(update, context)
        elif text == "💬 Чат с GPT":
            await handle_gpt_request(update, context)
        elif text == "⭐ Мои локации":
            await show_saved_locations(update, context)
        elif text == "⚙️ Помощь":
            await help_command(update, context)
        elif text == "🔙 Назад":
            await show_main_menu(update)
        else:
            # Проверяем, не является ли текст названием сохранённой локации
            locations = load_locations(update.effective_user.id)
            if text in locations:
                lat, lon = locations[text]
                plot = await generate_weather_plot(lat, lon, WEATHER_API_KEY)
                await update.message.reply_photo(
                    photo=plot,
                    caption=f"Прогноз погоды для '{text}'"
                )
            else:
                await update.message.reply_text("Неизвестная команда. Используйте меню.")
    except Exception as e:
        logger.error(f"Error in handle_text: {e}")
        await error_handler(update, context)

def main():
    """Запуск бота"""
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)
        
        # Обработчик для работы с локациями
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^🏙️ По названию города$"), handle_weather_by_city),
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.Regex("^🗑️ Удалить место$"), delete_location_menu)
            ],
            states={
                WEATHER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_weather_by_city)],
                LOCATION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_user_location)],
                DELETE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_location_deletion)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        
        # Регистрация обработчиков
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("Бот запущен")
        app.run_polling()
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
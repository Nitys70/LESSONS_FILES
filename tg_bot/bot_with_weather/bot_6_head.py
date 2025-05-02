import openai
import os
import requests
from datetime import datetime
import logging

import json


from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
# from config import TELEGRAM_TOKEN, OPENAI_API_KEY, AUTH_PASSWORD
from weather import generate_weather_plot
from locations import load_locations, save_location, delete_location

# Токены
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")


# Глобальные переменные для логирования
user_logins = set()  # Множество уникальных пользователей за день
current_date = datetime.now().date()
user_links = set()   # Для хранения ссылок на пользователей

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
        
        # Запись в файл
        with open('daily_users.txt', 'a') as f:
            f.write(f"{datetime.now()}: {user_id} | {user_link}\n")

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет авторизацию пользователя"""
    return context.user_data.get('authorized', False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с авторизацией"""
    await log_user(update)
    
    if not await check_auth(update, context):
        await update.message.reply_text(
            "🔒 Для использования бота введите пароль.\n"
            "Если у вас нет пароля, обратитесь к администратору."
        )
        return
    
    # Показываем основное меню после авторизации
    keyboard = [
        ["💬 Чат с GPT", "🌤️ Прогноз погоды"],
        ["⚙️ Помощь"]
    ]
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Главный обработчик текста с авторизацией"""
#     await log_user(update)
#     text = update.message.text
    
#     # Проверка авторизации
#     if not await check_auth(update, context):
#         if text == AUTH_PASSWORD:
#             context.user_data['authorized'] = True
#             await update.message.reply_text(
#                 "✅ Авторизация успешна!",
#                 reply_markup=ReplyKeyboardMarkup(
#                     [["💬 Чат с GPT", "🌤️ Прогноз погоды"]],
#                     resize_keyboard=True
#                 )
#             )
#             return
#         else:
#             await update.message.reply_text("❌ Неверный пароль. Попробуйте снова.")
#             return
    
#     # Обработка команд авторизованного пользователя
#     if text == "🌤️ Прогноз погоды":
#         await weather_menu(update, context)
#     elif text == "💬 Чат с GPT":
#         await handle_gpt_request(update, context)
#     # ... (остальная логика обработки)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)
    
    try:
        # Проверка авторизации
        if not await check_auth(update, context):
            if update.message.text == AUTH_PASSWORD:
                context.user_data['authorized'] = True
                await show_main_menu(update)
                return
            else:
                await update.message.reply_text("❌ Неверный пароль. Попробуйте ещё раз.")
                return  # Важно: остаёмся в режиме ввода пароля

        # Основная логика обработки команд
        text = update.message.text
        if text == "🌤️ Прогноз погоды":
            await weather_menu(update, context)
        elif text == "💬 Чат с GPT":
            await handle_gpt_request(update, context)
        else:
            await handle_regular_message(update, context)
            
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда статистики для админа"""
    if update.effective_user.id != 218553624:  # Замените на ваш ID
        await update.message.reply_text("🚫 Доступ запрещён")
        return
    
    stats_msg = (
        f"📊 Статистика за {datetime.now().date()}:\n"
        f"Уникальных пользователей: {len(user_logins)}\n"
        f"Список: {', '.join(user_links)}"
    )
    await update.message.reply_text(stats_msg)

async def show_main_menu(update: Update):
    keyboard = [
        ["💬 Чат с GPT", "🌤️ Прогноз погоды"],
        ["⚙️ Помощь"]
    ]
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
async def weather_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📍 По текущему местоположению", "🏙️ По названию города"],
        ["⭐ Мои сохранённые места", "🔙 Назад"]
    ]
    await update.message.reply_text(
        "Выберите способ получения прогноза погоды:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        
async def handle_gpt_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функционал GPT-чата будет реализован позже.")
    
async def handle_regular_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я не понимаю эту команду. Пожалуйста, используйте меню.")
    
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    await update.message.reply_text(f"Получены координаты: {location.latitude}, {location.longitude}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    logger.info("Бот запущен с авторизацией и логированием")
    app.run_polling()
    
    
    
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

print("1. Скрипт начал выполнение")  # Проверка запуска

logging.basicConfig(level=logging.DEBUG)  # Включите подробные логи

# TELEGRAM_TOKEN = "ВАШ_ТОКЕН"  # Вставьте реальный токен

print("2. Токен загружен")  # Проверка чтения токена

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("3. Команда /start получена")  # Проверка вызова обработчика
    await update.message.reply_text("Бот жив!")

print("4. Функции объявлены")  # Проверка парсинга кода

def main():
    print("5. Вход в main()")  # Проверка вызова main
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    print("6. Приложение создано")  # Проверка инициализации бота
    app.add_handler(CommandHandler("start", start))
    print("7. Обработчики добавлены")  # Проверка конфигурации
    app.run_polling()
    print("8. Бот запущен")  # Эта строка НЕ выполнится до остановки бота

if __name__ == "__main__":
    print("9. Запуск из __main__")  # Проверка точки входа
    main()
    print("10. После main()")  # Проверка завершения

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Инициализация логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация (ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ДАННЫЕ)
# TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"  # Формат: "1234567890:ABCdefGHIJKlmNoPQRsTUVwxyZ"
# AUTH_PASSWORD = "1206"

# Глобальные переменные
user_logins = set()
current_date = datetime.now().date()

async def show_main_menu(update: Update):
    keyboard = [
        ["💬 Чат с GPT", "🌤️ Прогноз погоды"],
        ["⚙️ Помощь"]
    ]
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Новый пользователь: {user_id}")
    
    if not context.user_data.get('authorized', False):
        await update.message.reply_text("🔒 Введите пароль для доступа:")
        return
    
    await show_main_menu(update)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Проверка авторизации
    if not context.user_data.get('authorized', False):
        if text == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            await update.message.reply_text("✅ Авторизация успешна!")
            await show_main_menu(update)
        else:
            await update.message.reply_text("❌ Неверный пароль")
        return
    
    # Обработка команд
    if text == "🌤️ Прогноз погоды":
        generate_weather_plot(lat='56.48', lon='84.98')
        # await update.message.reply_text("Функция погоды в разработке")
    elif text == "💬 Чат с GPT":
        await update.message.reply_text("Функция чата в разработке")
    else:
        await update.message.reply_text("Неизвестная команда")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Обработка геолокации пока не реализована")

def main():
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.LOCATION, handle_location))
        
        logger.info("Бот запускается...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
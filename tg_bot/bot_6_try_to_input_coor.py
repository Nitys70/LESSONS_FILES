import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import logging
from datetime import datetime
from internal_data import TELEGRAM_BOT_TOKEN
from internal_data import OPENAI_API_KEY

print(1)
# Токены
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_logs.log'
)
logger = logging.getLogger(__name__)

AUTH_PASSWORD = "1206"   # Пароль для авторизации

user_logins = set()  # Множество уникальных пользователей за день
current_date = datetime.now().date()  # Текущая дата для логирования
user_links = set() # МОЯ ДОРАБОТКА ссылнки на пользователей

# Настройка клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Константы
MAX_HISTORY_LENGTH = 10  # Максимальное количество пар вопрос-ответ в истории

hello_message = "Привет! Твой пароль верен, добро пожаловать! " + \
    "Я бот ChatGPT, и я могу помочь тебе в разных вопросах, только спроси :) " + \
        "К сожалению, я не умею искать в интернете информацию, но, если ты напишешь <code>погода</code>, " + \
            "это активирует моего товарища, и он тебе обязательно подскажет прогноз."
    
print(2)

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, авторизован ли пользователь."""
    user_id = update.effective_user.id
    if 'authorized' not in context.user_data:
        context.user_data['authorized'] = False
    return context.user_data['authorized']


async def log_user(update: Update):
    """Логирует уникальных пользователей."""
    global current_date, user_logins
    
    # Если наступил новый день, очищаем логи
    today = datetime.now().date()
    if today != current_date:
        user_logins.clear()
        current_date = today
    
    user_id = update.effective_user.id
    user_link = update.effective_user.link
    if user_id not in user_logins:
        user_logins.add(user_id)
        user_links.add(user_link)
        logger.info(f"New user login: {user_id}, New user link: {user_link}")
        # Записываем в файл для долгосрочного хранения
        with open('daily_users.txt', 'a') as f:
            f.write(f"{datetime.now()}: {user_id} - {user_link}\n")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Инициализируем историю диалога для пользователя

    if not await check_auth(update, context):
        await update.message.reply_text("Привет! Для использования бота введите пароль.\n"
                "Если у вас нет пароля, обратитесь к администратору."
            )
        
        return 

    
    context.user_data['conversation_history'] = []
    await update.message.reply_text("Привет! Я ChatGPT бот. Давай общаться! 🤖")
print(3)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)
    
    user_message = update.message.text.strip()

    # Проверка авторизации
    if not await check_auth(update, context):
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            await update.message.reply_text(hello_message, parse_mode="HTML")
            # Инициализируем историю диалога после авторизации
            context.user_data['conversation_history'] = []
            return
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте еще раз.")
            return

    # Ожидаем координаты
    if context.user_data.get('waiting_for_coords'):
        try:
            # Попытка разделить координаты (широта и долгота)
            lat, lon = map(float, user_message.split())
            context.user_data['waiting_for_coords'] = False  # Завершаем ожидание координат
            weather_image = weather(lat, lon)  # Получаем изображение с прогнозом
            await update.message.reply_photo(weather_image)
        except ValueError:
            # Если не удается распарсить координаты
            await update.message.reply_text("⚠️ Неверный формат координат. Введите в виде: 56.48 84.98")
        return

    # Запрос погоды
    if user_message.lower() == "погода":
        await update.message.reply_text("Пожалуйста, пришли координаты в формате 'Широта Долгота', например: 56.48 84.98")
        context.user_data['waiting_for_coords'] = True
        return

    # Остальная логика для общения с ChatGPT
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []

    # Добавляем новое сообщение пользователя в историю
    context.user_data['conversation_history'].append({"role": "user", "content": user_message})

    try:
        # Формируем messages для OpenAI
        messages = [{"role": "system", "content": "Ты дружелюбный помощник."}]
        messages.extend(context.user_data['conversation_history'])

        # Отправляем запрос к OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        reply = response.choices[0].message.content.strip()

        # Добавляем ответ ассистента в историю
        context.user_data['conversation_history'].append({"role": "assistant", "content": reply})

        # Ограничиваем длину истории, чтобы не превысить лимит токенов
        if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"OpenAI error: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вашего сообщения.")

print(4)


# Функция для получения статистики
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения статистики (только для админа)"""
    if update.effective_user.id != 218553624:  # Замените на ваш ID в Telegram
        await update.message.reply_text("У вас нет прав для просмотра статистики.")
        return
    
    unique_users = len(user_logins)
    await update.message.reply_text(f"Сегодня бота посетило {unique_users} уникальных пользователей. Вот список {user_links}")

# def weather():
#     print('Модуль в разработке')
#     return 'Модуль в разработке'
#     # return ('snow_forecast.jpg')
print(5)

def weather(lat: str, lon: str):
    import requests 
    import pandas as pd 
    from datetime import datetime
    # from internal_data import weather_api
    import seaborn as sns
    import matplotlib.pyplot as plt
    from io import BytesIO
    
    try:
        url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={weather_api}&lang=ru'
        response = requests.get(url)
        data = response.json()

        forecast_df = pd.DataFrame(data['hourly'])
        
        # Конвертация времени
        forecast_df['dt'] = forecast_df['dt'].apply(
            lambda ts: datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M'))
        
        # Создаем график
        plt.figure(figsize=(14, 6))
        plt.plot(forecast_df['dt'], forecast_df['temp'], marker='o')
        plt.grid()
        plt.title(f'Прогноз температуры для координат {lat}, {lon}')
        plt.xticks(rotation=90)
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        print(f"Weather API error: {e}")
        # Возвращаем изображение с ошибкой
        plt.figure(figsize=(10, 2))
        plt.text(0.5, 0.5, "Ошибка при получении данных о погоде", 
                ha='center', va='center')
        plt.axis('off')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
    
print(6)

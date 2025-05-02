import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import logging
from datetime import datetime
from internal_data import TELEGRAM_BOT_TOKEN
from internal_data import OPENAI_API_KEY
import time
import asyncio




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
    

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, авторизован ли пользователь."""
    user_id = update.effective_user.id
    if 'authorized' not in context.user_data:
        context.user_data['authorized'] = False
    return context.user_data['authorized']


async def log_user(update: Update):
    """Логирует уникальных пользователей."""
    global current_date, user_logins, user_links
    
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)
    
    # Проверка авторизации
    if not await check_auth(update, context):
        user_message = update.message.text
        
        # Проверяем, не ввел ли пользователь пароль
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            await update.message.reply_text(hello_message, parse_mode="HTML")
            # Инициализируем историю диалога после авторизации
            context.user_data['conversation_history'] = []
            return
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте еще раз.")
            return    
    
    # Основная логика обработки сообщений   
    user_message = update.message.text
    if user_message.lower().strip() == 'погода':
        await update.message.reply_text('Напиши, пожалуйста, город')
        user_message = update.message.text
        await asyncio.sleep(10)
        print(user_message)
        await update.message.reply_photo(weather())
        # weather()
    else:
    # Инициализируем историю, если её нет
        if 'conversation_history' not in context.user_data:
            context.user_data['conversation_history'] = []

        # Добавляем новое сообщение пользователя в историю
        context.user_data['conversation_history'].append({"role": "user", "content": user_message})

        try:
            # Формируем messages для OpenAI:
            # Начинаем с system-сообщения (необязательно, но помогает задать поведение бота)
            messages = [{"role": "system", "content": "Ты дружелюбный помощник."}]
            
            # Добавляем историю диалога
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
                # Оставляем только последние MAX_HISTORY_LENGTH пар вопрос-ответ
                context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

            await update.message.reply_text(reply)

        except Exception as e:
            print(f"OpenAI error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке вашего сообщения.")


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

def weather():
    print('Модуль в разработке')
    # return 'Модуль в разработке'
    # return ('snow_forecast.jpg')
    import requests 
    import pandas as pd 
    import json
    from datetime import datetime
    from internal_data import weather_api
    import seaborn as sns
    import matplotlib.pyplot as plt
    from io import BytesIO
    from telegram import Update
    
    # Tomsk city center:
    lat = '56.48'
    lon = '84.98'

    # Sabetta plant area
    # lat = '71.26'
    # lon = '72.05'

    # Krasnodar
    # lat = '45.02'
    # lon = '38.59'

    url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units={'metric'}&appid={weather_api}&lang={'ru'}'

    response = requests.get(url)

    data = response.json()

    # !!!!!!!!! Есть проблемы с изменение тибличных данных. Появлиась вероятность, меняются дождь снег

    forecast_df = pd.DataFrame(data['hourly'])

    feats_to_convert = ['dt']


    def ts_convert(ts):
        return datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M:%S')

    for feat in feats_to_convert:
        forecast_df[feat] = forecast_df[feat].apply(ts_convert)
        

    def description_extract(data):

        result = f'{data[0]['main']} : {data[0]['description']}'

        return result
        
    forecast_df['info'] = forecast_df['weather'].apply(description_extract)

    forecast_df = forecast_df.drop('weather', axis=1)

    # Преобразование признаков осадков (изначально словарь либо None)
    # forecast_df['rain'] = forecast_df['rain'].apply(lambda x: 
    #     list(x.values())[0] if type(x) is dict else 0
    #     )

    # forecast_df['snow'] = forecast_df['snow'].apply(lambda x: 
    #     list(x.values())[0] if type(x) is dict else 0
    #     )



    plt.figure(figsize=(14,6))

    line_graph = sns.lineplot(
        data = forecast_df, 
        x = 'dt',
        y = 'temp'
        )

    line_graph.grid()

    line_graph.set_ylabel('Температура воздуха', fontsize = 16)
    line_graph.set_xlabel('')
    plt.tick_params(axis='x', labelrotation = 90)

    line_title_name = f'Прогноз температуры за период \
        {forecast_df.iloc[0]['dt']} - {forecast_df.iloc[47]['dt']}'

    line_graph.set_title(line_title_name, fontsize = 16)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    print("ЗАпрашивали погоду")
    
    
    ######################
    
    plt.subplots(figsize = (14,6))

    hist_gust = sns.barplot(
        data = forecast_df,
        x = 'dt', 
        y='wind_gust',
        color='orange'
    )

    hist_wind = sns.barplot(
        data = forecast_df,
        x = 'dt', 
        y='wind_speed',
        color='blue'
    )

    plt.grid()

    plt.tick_params(axis='x', labelrotation = 90)

    plt.legend([hist_gust, hist_wind], ['Порывы ветра', 'Скорость ветра'])
    
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    print("ЗАпрашивали погоду_2")
    
    #######################
    
    return buf


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
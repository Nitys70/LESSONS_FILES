import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import requests
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_logs.log'
)
logger = logging.getLogger(__name__)

# Токены
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TELEGRAM_BOT_TOKEN = "das"
OPENAI_API_KEY = "sA"
AUTH_PASSWORD = "6"

# Настройка клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Константы
MAX_HISTORY_LENGTH = 10  # Максимальное количество пар вопрос-ответ в истории

# Глобальные переменные для логирования
user_logins = set()  # Множество уникальных пользователей за день
current_date = datetime.now().date()  # Текущая дата для логирования
user_links = set() # МОЯ ДОРАБОТКА ссылнки на пользователей

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
    # Закомменчено в связи с блоком кода ниже
    # context.user_data['conversation_history'] = []
    # await update.message.reply_text("Привет! Я ChatGPT бот. Давай общаться! 🤖")

    """Обработчик команды /start."""
    await log_user(update)
    
    if not await check_auth(update, context):
        await update.message.reply_text(
            "Привет! Для использования бота введите пароль.\n"
            "Если у вас нет пароля, обратитесь к администратору."
        )
        return
    
    # Инициализируем историю диалога для пользователя
    context.user_data['conversation_history'] = []
    await update.message.reply_text("Привет! Я Chat-GPT бот! 🤖" +
                                    " Ты можешь задать мне любые вопросы, или обсудить что-то." +
                                    "Буду рад, если смогу помочь :)" + 
                                    "А еще я смогу подсказать тебе прогноз погоды, " +
                                    "если ты напишешь слово погода")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    await log_user(update)
    
    # Проверка авторизации
    if not await check_auth(update, context):
        user_message = update.message.text
        
        # Проверяем, не ввел ли пользователь пароль
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            await update.message.reply_text("Авторизация успешна! Теперь вы можете пользоваться ботом.")
            # Инициализируем историю диалога после авторизации
            context.user_data['conversation_history'] = []
            return
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте еще раз.")
            return
        
    user_message = update.message.text
    
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

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения статистики (только для админа)"""
    if update.effective_user.id != 218553624:  # Замените на ваш ID в Telegram
        await update.message.reply_text("У вас нет прав для просмотра статистики.")
        return
    
    unique_users = len(user_logins)
    await update.message.reply_text(f"Сегодня бота посетило {unique_users} уникальных пользователей. Вот список {user_links}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
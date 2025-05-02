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

# Токены (ЗАМЕНИТЕ НА РЕАЛЬНЫЕ!)
TELEGRAM_BOT_TOKEN = "Y"  # Получите у @BotFather
OPENAI_API_KEY = "skA"        # Из панели OpenAI
AUTH_PASSWORD = "s"  # Пароль для доступа к боту

# Настройка клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Константы
MAX_HISTORY_LENGTH = 10

# Глобальные переменные
user_logins = set()
current_date = datetime.now().date()
user_links = set()

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет авторизацию пользователя."""
    return context.user_data.get('authorized', False)

async def log_user(update: Update):
    """Логирует пользователей."""
    global current_date, user_logins
    
    today = datetime.now().date()
    if today != current_date:
        user_logins.clear()
        current_date = today
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    if user_id not in user_logins:
        user_logins.add(user_id)
        user_links.add(f"@{username}" if username else str(user_id))
        logger.info(f"New user: {user_id}")
        with open('daily_users.txt', 'a') as f:
            f.write(f"{datetime.now()}: {user_id}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""
    await log_user(update)
    
    if not await check_auth(update, context):
        await update.message.reply_text(
            "Привет! Для доступа к боту введите пароль.\n"
            "Если у вас нет пароля, обратитесь к администратору."
        )
        return
    
    context.user_data['conversation_history'] = []
    await update.message.reply_text(
        "Привет! Я Chat-GPT бот! 🤖\n"
        "Задавайте любые вопросы или обсуждайте темы.\n"
        "Также могу подсказать прогноз погоды по слову 'погода'"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений."""
    print(f"DEBUG: Получено сообщение: {update.message.text}")  # Логирование
    
    await log_user(update)
    
    # Проверка авторизации
    if not await check_auth(update, context):
        if update.message.text == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            context.user_data['conversation_history'] = []
            await update.message.reply_text("✅ Авторизация успешна!")
            return
        else:
            await update.message.reply_text("❌ Неверный пароль!")
            return
    
    # Инициализация истории
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []

    try:
        # Формируем запрос к OpenAI
        context.user_data['conversation_history'].append(
            {"role": "user", "content": update.message.text}
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты дружелюбный помощник."},
                *context.user_data['conversation_history']
            ],
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
        
        # Обновляем историю
        context.user_data['conversation_history'].append(
            {"role": "assistant", "content": reply}
        )
        
        # Ограничиваем длину истории
        if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика для админа."""
    if update.effective_user.id != 218553624:  # Замените на ваш ID
        await update.message.reply_text("❌ Доступ запрещён!")
        return
    
    await update.message.reply_text(
        f"📊 Статистика:\n"
        f"Уникальных пользователей: {len(user_logins)}\n"
        f"Список: {', '.join(user_links)}"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
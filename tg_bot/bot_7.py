import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
from datetime import datetime
import json

# Токены
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Константы
MAX_HISTORY_LENGTH = 10  # Максимальное количество пар вопрос-ответ в истории
LOG_FILE = "bot_users.log"  # Файл для логов пользователей

def log_user(user_id: int, username: str, first_name: str):
    """Логирует нового пользователя в файл"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data = {
        "timestamp": timestamp,
        "user_id": user_id,
        "username": username,
        "first_name": first_name
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(user_data, ensure_ascii=False) + "\n")

def count_unique_users():
    """Подсчитывает количество уникальных пользователей в логах"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            users = set()
            for line in f:
                try:
                    user_data = json.loads(line)
                    users.add(user_data["user_id"])
                except json.JSONDecodeError:
                    continue
            return len(users)
    except FileNotFoundError:
        return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Логируем нового пользователя
    log_user(user.id, user.username, user.first_name)
    
    # Инициализируем историю диалога
    context.user_data['conversation_history'] = []
    await update.message.reply_text(f"Привет, {user.first_name}! Я ChatGPT бот. Давай общаться! 🤖")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Инициализируем историю, если её нет
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
        context.user_data['conversation_history'].append({"role": "assistant", "content": reply})

        # Ограничиваем длину истории
        if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"OpenAI error: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вашего сообщения.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику бота"""
    unique_users = count_unique_users()
    await update.message.reply_text(
        f"📊 Статистика бота:\n"
        f"• Уникальных пользователей: {unique_users}\n"
        f"• Посмотреть логи: `cat {LOG_FILE}`"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
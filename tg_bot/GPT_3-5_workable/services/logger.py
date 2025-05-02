from telegram import Update
from datetime import datetime
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

LOG_FILE = "data/user_log.txt"
ADMIN_ID = 218553624

# Простое логирование пользователя (ID и имя)
async def log_user(update: Update):
    user = update.effective_user
    log_entry = f"{datetime.now()} - ID: {user.id}, Name: {user.full_name}, Username: @{user.username}\n"

    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

# Получение статистики за сегодня
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    today = datetime.now().date()
    users = set()

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    timestamp_str, rest = line.split(" - ", 1)
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    if timestamp.date() == today:
                        parts = rest.strip().split(", ")
                        username_part = next((p for p in parts if p.startswith("Username: @")), None)
                        username = username_part.replace("Username: ", "") if username_part else "(без ника)"
                        users.add(username)
                except Exception as e:
                    print(f"Ошибка при парсинге строки лога: {e}")

    message = f"Сегодня использовали бота {len(users)} человек(а):\n" + "\n".join(f"- {u}" for u in sorted(users))
    await update.message.reply_text(message or "Сегодня не было активности.")

from telegram import Update
from datetime import datetime
import os

LOG_FILE = "data/user_log.txt"

# Простое логирование пользователя (ID и имя)
async def log_user(update: Update):
    user = update.effective_user
    log_entry = f"{datetime.now()} - ID: {user.id}, Name: {user.full_name}\n"

    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

from telegram import Update
from telegram.ext import ContextTypes

# Проверка авторизации пользователя
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get('authorized', False)

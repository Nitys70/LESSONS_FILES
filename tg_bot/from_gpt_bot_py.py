import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import os

# Импорт авторизации, логирования и обработки сообщений
from config import TELEGRAM_BOT_TOKEN, AUTH_PASSWORD, MAX_HISTORY_LENGTH, hello_message
from services.auth import check_auth
from services.logger import log_user
from handlers import weather_handler

# === Настройка логирования ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# === Основной обработчик сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)

    user_message = update.message.text.strip()

    # Авторизация
    if not await check_auth(update, context):
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            context.user_data['conversation_history'] = []
            await update.message.reply_text(hello_message, parse_mode="HTML")
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте еще раз.")
        return

    # Инициализация истории, если нет
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []

    # Добавляем сообщение пользователя в историю
    context.user_data['conversation_history'].append({"role": "user", "content": user_message})

    try:
        # Подготовка запроса к OpenAI
        from openai import OpenAI
        client = OpenAI()

        messages = [{"role": "system", "content": "Ты дружелюбный помощник."}]
        messages.extend(context.user_data['conversation_history'])

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        reply = response.choices[0].message.content.strip()
        context.user_data['conversation_history'].append({"role": "assistant", "content": reply})

        # Обрезаем историю, если длинная
        if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вашего сообщения.")


# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите пароль для доступа.")


# === Запуск бота ===
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ConversationHandler для запроса погоды
    weather_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(погода|Погода)$"), weather_handler.start_weather)
        ],
        states={
            weather_handler.CHOOSE_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, weather_handler.handle_location)
            ],
            weather_handler.CONFIRM_SAVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, weather_handler.handle_confirmation)
            ],
        },
        fallbacks=[CommandHandler("отмена", weather_handler.cancel)],
    )

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(weather_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск
    application.run_polling()


if __name__ == '__main__':
    main()

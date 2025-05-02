import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")
MAX_HISTORY_LENGTH = 10
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from services.auth import check_auth
from services.logger import log_user, show_stats
from handlers.weather_handler import weather_conversation_handler

from openai import OpenAI

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Приветственное сообщение
hello_message = "👋 Добро пожаловать! Я чат-бот GPT-4.1-mini." + \
    "Cо мной ты можешь обсудить практически все темы, а так же задать интересующий тебя вопрос. " + \
    "Я очень постараюсь тебе помочь 🙏 \n" + \
    "К сожалению, я не умею делать поиск в интернете, но, я могу помочь тебе с прогнозом погоды ⛅️ \n" +\
    "Просто напиши слово <code>погода</code>, это активирует моего товарища, и он тебе поможет"

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)
    await update.message.reply_text("Введите пароль для доступа к боту:")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)

    user_message = update.message.text.strip()

    # Проверка авторизации
    if not await check_auth(update, context):
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            context.user_data['conversation_history'] = []
            await update.message.reply_text(hello_message, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Неверный пароль. Попробуйте снова.")
        return

    # Проверка наличия истории
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []

    # Добавим сообщение пользователя в историю
    context.user_data['conversation_history'].append({"role": "user", "content": user_message})

    try:
        messages = [{"role": "system", "content": "Ты дружелюбный помощник."}]
        messages.extend(context.user_data['conversation_history'])

        response = client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=messages,
            temperature=0.9,
            max_tokens=1000,
            )

        reply = response.choices[0].message.content.strip()

        # Добавим ответ в историю
        context.user_data['conversation_history'].append({"role": "assistant", "content": reply})

        # Урежем историю при необходимости
        if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

        await update.message.reply_text(reply)

    except Exception as e:
        logging.exception("Ошибка OpenAI")
        await update.message.reply_text("⚠️ Ошибка при обращении к OpenAI. Попробуйте позже.")


# Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем ConversationHandler для погоды
    app.add_handler(weather_conversation_handler)

    # Команды
    app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("stats", show_stats))

    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()

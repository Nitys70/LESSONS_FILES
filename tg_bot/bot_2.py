import logging
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔐 Твои ключи
TELEGRAM_BOT_TOKEN = ""
OPENAI_API_KEY = ""

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Установка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

# ✨ Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Отправляем сообщение в OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # или "gpt-4", если есть доступ
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1000,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к ChatGPT.")

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши мне что-нибудь, и я отвечу как ChatGPT 🤖")

# 🚀 Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

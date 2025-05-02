import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

# Токены
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка клиента OpenAI (новый стиль)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Переменная для хранения истории общения
conversation_history = []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_history
    conversation_history = []
    await update.message.reply_text("Привет! Напиши мне что-нибудь, и я отвечу как ChatGPT 🤖")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_history
    user_message = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            temperature=0.7,
            max_tokens=1000,
            history=conversation_history
        )
        reply = response.choices[0].message.content.strip()
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        print(f"OpenAI ошибка: {e}")
        await update.message.reply_text("Ошибка при обращении к ChatGPT.")

# Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if name == "main":
    main()
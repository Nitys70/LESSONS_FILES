# import os
# import tempfile
# from openai import OpenAI
# from telegram import Update
# from telegram.ext import Application, MessageHandler, filters, ContextTypes

# # Укажи свои ключи
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_AUDIO")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_AUDIO")

# # Инициализация клиента OpenAI
# client = OpenAI(api_key=OPENAI_API_KEY)


# # Обработчик голосовых сообщений
# async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     file = await update.message.voice.get_file()

#     # Сохраняем временно голосовой файл
#     with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tf:
#         file_path = tf.name
#         await file.download_to_drive(file_path)

#     # Отправляем в OpenAI Whisper для транскрибации
#     with open(file_path, "rb") as audio_file:
#         transcript = client.audio.transcriptions.create(
#             model="whisper-1",
#             file=audio_file
#         )

#     # Отправляем пользователю результат
#     await update.message.reply_text(transcript.text)

#     # Удаляем временный файл
#     os.remove(file_path)


# def main():
#     app = Application.builder().token(TELEGRAM_TOKEN).build()

#     # Обрабатываем только голосовые сообщения
#     app.add_handler(MessageHandler(filters.VOICE, voice_handler))

#     print("Бот запущен...")
#     app.run_polling()


# if __name__ == "__main__":
#     main()
    
    
import os
import tempfile
from datetime import datetime
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Загружаем ключи из окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_AUDIO")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_AUDIO")

client = OpenAI(api_key=OPENAI_API_KEY)


# Обработчик голосовых сообщений
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()

    # Сохраняем временно голосовой файл
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tf:
        file_path = tf.name
        await file.download_to_drive(file_path)

    # Шаг 1: Whisper → транскрибация
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    text = transcript.text

    # Шаг 2: GPT → структурирование текста
    today = datetime.now().strftime("%d.%m.%Y")
    prompt = f"""
Ты парсишь текст поездки и возвращаешь JSON с такими полями:
- date: дата поездки (если нет в тексте — {today})
- origin: адрес отправления (с указанием населенного пункта)
- destination: адрес назначения (с указанием насленного пункта)
- passengers: количество пассажиров (по умолчанию 1)
- waiting_time: время, которое пользователь готов ожидать (по умолчанию 15 минут)
- details: дополнительные детали (багаж, животные и т.п.)

Текст: "{text}"
Верни только JSON, без комментариев и пояснений.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты помощник, который структурирует поездки."},
            {"role": "user", "content": prompt}
        ]
    )

    structured = response.choices[0].message.content

    # Отправляем пользователю
    reply_message = f"📌 Информация о поездке:\n\n{structured}"
    await update.message.reply_text(reply_message)

    # Удаляем временный файл
    os.remove(file_path)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обрабатываем голосовые сообщения
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
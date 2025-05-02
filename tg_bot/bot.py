import logging
import requests
from telegram.update import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Укажи свой API токен бота, полученный от BotFather
TELEGRAM_API_TOKEN = '7OA'

# Укажи API ключ для работы с GPT-4o Mini
GPT_API_KEY = 'sk6o56AA'

# URL для отправки запросов к GPT-4o Mini
GPT_API_URL = 'https://api.openai.com/v1/completions'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я бот, готов общаться с GPT-4o Mini. Напиши мне что-нибудь!')

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Напиши мне вопрос, и я передам его GPT-4o Mini.')

def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text

    # Отправка запроса к GPT-4o Mini
    headers = {
        'Authorization': f'Bearer {GPT_API_KEY}',
        'Content-Type': 'application/json',
    }

    data = {
        'model': 'gpt-4o-mini',  # Или другой нужный тебе параметр
        'messages': [{'role': 'user', 'content': user_message}],
        'max_tokens': 150
    }

    response = requests.post(GPT_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        gpt_response = response.json()
        message = gpt_response['choices'][0]['message']['content']
        update.message.reply_text(message)
    else:
        update.message.reply_text('Произошла ошибка при обработке запроса.')

def main():
    # Создаем Updater и передаем ему API токен
    updater = Updater(TELEGRAM_API_TOKEN)

    # Получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчики команд и сообщений
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()

    # Работает до тех пор, пока не завершится
    updater.idle()

if __name__ == '__main__':
    main()

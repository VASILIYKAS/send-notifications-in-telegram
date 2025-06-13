import os
import logging
import requests
import time
from logging.handlers import RotatingFileHandler
from textwrap import dedent
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext
)
from dotenv import load_dotenv


logger = logging.getLogger("TelegramBot")
logger.setLevel(logging.INFO)

os.makedirs('logs', exist_ok=True)

file_handler = RotatingFileHandler(
    'bot.log',
    maxBytes=1024*1024,
    backupCount=3,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)


def send_log_to_telegram(context: CallbackContext, message: str):
    context.bot.send_message(
        chat_id=os.environ['chat_id'],
        text=f"Бот лог: {message}"
    )


def check_reviews(update: Update, context: CallbackContext):
    dvmn_api_key = os.environ['DVMN_API_KEY']
    long_polling_url = 'https://dvmn.org/api/long_polling/'
    last_timestamp = None

    while True:
        try:
            params = {'timestamp': last_timestamp} if last_timestamp else {}
            headers = {'Authorization': f'Token {dvmn_api_key}'}

            response = requests.get(
                long_polling_url,
                headers=headers,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            review_status = response.json()

            if review_status['status'] == 'found':
                for attempt in review_status['new_attempts']:
                    lesson_title = attempt['lesson_title']
                    status = (
                        'Принята' if not attempt['is_negative']
                        else 'Требует доработки'
                    )
                    text = (
                        f'Работа: {lesson_title}\n'
                        f'Статус: {status}\n'
                        f"Ссылка: {attempt['lesson_url']}"
                    )
                    context.bot.send_message(
                        chat_id=os.environ['chat_id'],
                        text=text
                    )

                last_timestamp = review_status['last_attempt_timestamp']

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            error_message = "Ошибка подключения, повторная попытка через 5 секунд"
            logger.warning(error_message)
            send_log_to_telegram(context, error_message)
            time.sleep(5)
            continue
        except requests.exceptions.HTTPError as e:
            error_message = f"Ошибка: {e.response.status_code}"
            logger.error(error_message)
            send_log_to_telegram(context, error_message)
            return {'status': 'error', 'error': f"Ошибка API: {e.response.status_code}"}


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        dedent("""
        Привет! Я бот для уведомлений о проверке работ на dvmn.org.
        Буду присылать тебе уведомления о статусе проверки твоих работ.
        """)
    )

    check_reviews(update, context)


def error_handler(update: Update, context: CallbackContext):
    error_msg = f"Ошибка: {context.error}"
    logger.error(error_msg)

    context.bot.send_message(
        chat_id=os.environ['chat_id'],
        text=f"Ошибка в боте: {error_msg}"
    )


def main():
    load_dotenv()
    token = os.environ['TG_BOT_TOKEN']
    if not token:
        error_message = dedent("""
            Ошибка: Не указан TG_BOT_TOKEN.
            Убедитесь, что он задан в переменных окружения.
        """)
        logger.error(error_message)
        return

    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_error_handler(error_handler)

    startup_message = "Бот успешно запущен!"
    logger.info(startup_message)

    updater.start_polling()

    updater.bot.send_message(
            chat_id=os.environ['chat_id'],
            text=startup_message
        )

    updater.idle()

if __name__ == '__main__':
    main()
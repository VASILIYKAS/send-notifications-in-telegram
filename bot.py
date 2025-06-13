import os
import requests
import time
from textwrap import dedent
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext
)
from dotenv import load_dotenv
from logger import setup_logger


logger = setup_logger('Notifications bot')


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
            logger.warning("Ошибка подключения, повтор через 5 сек", exc_info=True)
            time.sleep(5)
            continue
        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP Error {e.response.status_code}"
            logger.error(error_message, exc_info=True)
            return {'status': 'error', 'error': error_message}
        except Exception:
            logger.critical("Критическая ошибка", exc_info=True)
            raise


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        dedent("""
        Привет! Я бот для уведомлений о проверке работ на dvmn.org.
        Буду присылать тебе уведомления о статусе проверки твоих работ.
        """)
    )

    check_reviews(update, context)


def main():
    try:
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

        logger.info("Бот успешно запущен!")

        updater.start_polling()
        updater.idle()

    except Exception as e:
        logger.critical(e, exc_info=True)
        raise

if __name__ == '__main__':
    main()
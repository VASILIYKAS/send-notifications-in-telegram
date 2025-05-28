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


def check_reviews(
        dvmn_api_key: str,
        long_polling_url: str,
        last_timestamp: str = ''
):
    params = {'timestamp': last_timestamp} if last_timestamp else {}
    headers = {'Authorization': f'Token {dvmn_api_key}'}

    response = requests.get(
        long_polling_url,
        headers=headers,
        params=params,
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def start(update: Update, context: CallbackContext) -> None:
    context.chat_data['last_timestamp'] = None

    update.message.reply_text(
        dedent("""
        Привет! Я бот для уведомлений о проверке работ на dvmn.org.
        Буду присылать тебе уведомления о статусе проверки твоих работ.
        """)
    )

    context.job_queue.run_repeating(
        check_reviews_job,
        interval=60,
        first=2,
        context={'last_timestamp': None}
    )


def check_reviews_job(context: CallbackContext) -> None:
    job_context = context.job.context
    last_known_timestamp = job_context.get('last_timestamp')

    try:
        api_data = check_reviews(
            dvmn_api_key=os.environ['DVMN_API_KEY'],
            long_polling_url='https://dvmn.org/api/long_polling/',
            last_timestamp=last_known_timestamp
        )

        if api_data['status'] == 'found':
            for attempt in api_data['new_attempts']:
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

            job_context['last_timestamp'] = api_data.get('last_attempt_timestamp')

    except requests.exceptions.ReadTimeout:
        return {'status': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'status': 'error', 'error': 'Ошибка соединения с сервером'}
        time.sleep(5)
    except requests.exceptions.HTTPError as e:
        return {'status': 'error', 'error': f"Ошибка API: {e.response.status_code}"}


def main():
    load_dotenv()
    token = os.environ['TG_BOT_TOKEN']
    if not token:
        print(dedent("""
            Ошибка: Не указан TG_BOT_TOKEN.
            Убедитесь, что он задан в переменных окружения.
        """))
        return

    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))

    updater.start_polling()
    print('Бот запущен!')
    updater.idle()


if __name__ == '__main__':
    main()
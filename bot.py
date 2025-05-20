import os
import requests
import time
from textwrap import dedent
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext
)
from dotenv import load_dotenv
from libs.api_client import check_reviews


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
        interval=30,
        first=2,
        context=context.chat_data
    )


def check_reviews_job(context: CallbackContext) -> None:
    job_context = context.job.context
    last_known_timestamp = job_context.get('last_timestamp')

    try:
        api_response = check_reviews(
            dvmn_api_key=os.getenv('DVMN_API_KEY'),
            long_polling_url='https://dvmn.org/api/long_polling/',
            last_timestamp=last_known_timestamp
        )

    except requests.exceptions.ReadTimeout:
        return {'status': 'timeout'}
    except requests.exceptions.ConnectionError:
        time.sleep(5)
        return {'status': 'connection_error'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

    if not api_response:
        print('Нет ответ от API')
        return

    if api_response['status'] == 'found':
        for review_attempt in api_response['attempts']:
            lesson_title = review_attempt['lesson_title']
            is_approved = not review_attempt['is_negative']
            status = 'Принята' if is_approved else 'Требует доработки'

            notification_text = (
                f'Работа: {lesson_title}\n'
                f'Статус: {status}\n'
                f'Ссылка: {review_attempt['lesson_url']}'
            )
            try:
                context.bot.send_message(
                    chat_id=1612767132,
                    text=notification_text
                )
            except NetworkError as e:
                print(f'Ошибка сети при отправке сообщения: {e}')
                time.sleep(5)
                return

        job_context['last_timestamp'] = api_response['timestamp']

    elif api_response['status'] == 'timeout':
        if 'timestamp' in api_response:
            job_context['last_timestamp'] = api_response['timestamp']
        print('Нет новых проверок')

    elif api_response['status'] == 'connection_error':
        print('Ошибка соединения с сервером')

    elif api_response['status'] == 'error':
        print(f'Ошибка API: {api_response.get('message', 'Неизвестная ошибка')}')


def main():
    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
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
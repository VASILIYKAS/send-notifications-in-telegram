import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

DVMN_API_KEY = os.getenv('DVMN_API_KEY')
LONG_POLLING_URL = 'https://dvmn.org/api/long_polling/'


def check_reviews(last_timestamp=None):
    params = {'timestamp': last_timestamp} if last_timestamp else {}
    headers = {'Authorization': f'Token {DVMN_API_KEY}'}

    try:
        response = requests.get(
            LONG_POLLING_URL,
            headers=headers,
            params=params,
            timeout=60
        )
        response.raise_for_status()
        work_status = response.json()
        new_timestamp = (
            work_status.get('last_attempt_timestamp')
            or work_status.get('timestamp_to_request')
        )

        if work_status['status'] == 'found':
            return {
                'status': 'found',
                'attempts': work_status['new_attempts'],
                'timestamp': new_timestamp
            }
        return {
            'status': work_status['status'],
            'timestamp': new_timestamp
        }

    except requests.exceptions.ReadTimeout:
        print('Нет ответа от сервера, ожидаем...')
        return {'status': 'timeout'}
    except requests.exceptions.ConnectionError:
        print('Пропало интернет соединение. Повторное соединение через 5 сек.')
        time.sleep(5)
        return {'status': 'connection_error'}
    except Exception as e:
        return print(f'Неизвестная ошибка: {str(e)}')
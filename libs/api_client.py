import requests
from dotenv import load_dotenv


def check_reviews(
        dvmn_api_key: str,
        long_polling_url: str,
        last_timestamp: float = None
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


def main():
    load_dotenv()
    last_timestamp = None

    while True:
        work_status = check_reviews(last_timestamp)

        if work_status['status'] == 'found':
            last_timestamp = work_status['timestamp']
        elif work_status['status'] == 'timeout':
            print('Нет ответа от сервера, ожидаем...')
        elif work_status['status'] == 'connection_error':
            print('Пропало интернет соединение. Повторное соединение через 5 сек.')
        elif work_status['status'] == 'error':
            print(f'Неизвестная ошибка: {work_status["message"]}')


if __name__ == '__main__':
    main()
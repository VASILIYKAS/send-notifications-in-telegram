# Бот для оповещения пользователя о проверке работ на [dvmn.org](https://dvmn.org).

Этот скрипт отправляет уведомления в Telegram о статусе проверки ваших работ на платформе dvmn.org. Для получения обновлений используется технология Long-polling.  

## Оглавление

- [Требования](#требования)
- [Установка](#установка)
  - [Переменный окружения](#переменный-окружения)
- [Использование](#использование)
- [Цель проекта](#цель-проекта)


## Требования

- Python 3.12
- `python-telegram-bot`
- `requests`
- `python-dotenv`
- `urllib3`


## Установка

- Скачайте код c репозитория.
- Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
source .venv/bin/activate  # для macOS/Linux
.\.venv\Scripts\activate   # для Windows

```
- Установите зависимости:
```bash
 pip install -r requirements.txt
```
### Переменный окружения
Создайте файл .env в корневой папке проекта и добавьте в него следующие переменные:
```python
TG_BOT_TOKEN=ваш_телеграм_бот_токен
chat_id=чат_id_вашего_канала
DVMN_API_KEY=ваш_api_ключ_dvmn
SEND_LOG_BOT_TOKEN=ваш_телеграм_бот_токен
```
- TG_BOT_TOKEN — токен вашего Telegram-бота. Получить можно у [BotFather](https://telegram.me/BotFather).
- chat_id — ID чата или пользователя, куда бот будет отправлять сообщения. Узнать можно через бота [userinfobot](https://telegram.me/userinfobot), отправив ему любое сообщение. В ответ вы получите цифровой ID или никнейм с @.
- DVMN_API_KEY — ключ API с личного кабинета на [dvmn.org](https://dvmn.org).
- SEND_LOG_BOT_TOKEN — токен вашего Telegram-бота который будет отправлять сообщения с ошибками и трейсбеком. Получить можно также у [BotFather](https://telegram.me/BotFather).

## Использование
Запустите бота командой:
```bash
python bot.py
```
После запуска бот войдёт в режим long-polling. Отправьте боту команду /start, чтобы он начал присылать уведомления. Когда на сервере появится обновление статуса вашей работы, бот отправит сообщение с названием работы, её текущим статусом и ссылкой.

## Цель проекта
Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).



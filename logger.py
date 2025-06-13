import logging
import os
import traceback
from logging.handlers import RotatingFileHandler
from telegram import Bot
from dotenv import load_dotenv


load_dotenv()


class TelegramLogHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.bot = Bot(token=os.environ['SEND_LOG_BOT_TOKEN'])
        self.chat_id = os.getenv('chat_id')

    def emit(self, record):
        try:
            formatted_record = self.format(record)
            if record.exc_info:
                text = '\n'.join(traceback.format_exception(*record.exc_info))
                formatted_record += f"\nTraceback:\n{text}"

            self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_record,
                parse_mode=None
            )

        except Exception as e:
            print(f"Ошибка при отправке лога: {e}")


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    os.makedirs('logs', exist_ok=True)

    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    telegram_handler = TelegramLogHandler()
    telegram_handler.setLevel(logging.ERROR)

    logger.addHandler(file_handler)
    logger.addHandler(telegram_handler)

    return logger
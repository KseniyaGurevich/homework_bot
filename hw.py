from telegram.ext import Updater
import telegram
import requests
import os
from dotenv import load_dotenv
import time
from pprint import pprint
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    stream=open(r'program.log', 'w', encoding='utf8'),
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    mode='a',
    maxBytes=50000000,
    backupCount=5,
    encoding='utf8',
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s'
)
handler.setFormatter(formatter)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение в Telegram отправлено!')
    except Exception as error:
        logger.error(f'Бот не смог отправить сообщение: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к API-сервису"""
    try:
        timestamp = current_timestamp
        params = {'from_date': timestamp}
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
        return api_answer.json()
    except Exception as error:
        send_message(bot, 'API не отвечает')
        logger.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверяет ответ API на корректность"""
    try:
        isinstance(response.get('homework'), dict)
        return response.get('homeworks')
    except Exception as error:
        send_message(bot, 'api не вернул словарь')
        logger.error(f'API не вернул словарь: {error}')




def parse_status(homework):
    """Извлекает из информации статус о конкретной домашней работе"""
    homework_name = homework[0].get('homework_name')
    homework_status = homework[0].get('status')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logger.error(f'Отсутсвие ожидаемых статусов: {error}')
        send_message(bot, 'Отсутсвие ожидаемых статусов')


def check_tokens():
    """Проверяет доступность переменных окружения"""
    check_tokens = [TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID]
    if all([token != None for token in check_tokens]) is True:
        return True
    else:
        return False



def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        send_message(bot, 'нет токенов')
        logger.critical('Отсутствие обязательных переменных окружения!')

    current_timestamp = 0
    response = get_api_answer(current_timestamp)
    homework = check_response(response)
    message = parse_status(homework)
    send_message(bot, message)

if __name__ == '__main__':
    main()
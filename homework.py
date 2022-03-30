import telegram
import requests
import os
from dotenv import load_dotenv
import time
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


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение в Telegram отправлено!')
    except Exception as error:
        logger.error(f'Бот не смог отправить сообщение: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к API-сервису"""
    logger.info('Проверяем ответ API')
    params = {'from_date': current_timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if api_answer.status_code != 200:
            logger.error('API возвращает код, отличный от 200')
            raise Exception('API возвращает код, отличный от 200')
        return api_answer.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
        raise


def check_response(response):
    """Проверяет ответ API на корректность"""
    if not isinstance(response, dict):
        raise TypeError('Oтвет API не является словарём')

    homeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if not (homeworks and current_date):
        raise KeyError('Нет ключей "homeworks" и "current_date" в словаре')

    if isinstance(homeworks[0], list):
        logger.error('ДЗ приходят в виде списка')
        raise TypeError('ДЗ приходят в виде списка')
    else:
        return homeworks


def parse_status(homework):
    """Извлекает из запроса к API статус о последней домашней работе"""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logger.error(f'Недокументированный статус домашней работы: {error}')
        raise


def check_tokens():
    """Проверяет доступность переменных окружения"""
    check_tokens = [TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID]
    if all([token != None for token in check_tokens]) is True:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    if check_tokens() is False:
        logger.critical('Отсутствие обязательных переменных окружения!')
        raise KeyError('Нет обязательных переменных окружения!')

    current_timestamp = 0
    last_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            if last_message != message:
                send_message(bot, message)
            else:
                logger.debug('статус не изменился')
                send_message(bot, 'статус не изменился')
            time.sleep(RETRY_TIME)
            last_message = message

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

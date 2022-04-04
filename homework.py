import sys
import telegram
import requests
import os
from dotenv import load_dotenv
import time
import logging
from http import HTTPStatus
import datetime
from exceptions import MyCustomError

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


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение в Telegram отправлено!')
    except MyCustomError as error:
        raise MyCustomError(f'Бот не смог отправить сообщение: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к API-сервису."""
    logging.info('Проверяем ответ API')
    params = {'from_date': current_timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if api_answer.status_code == HTTPStatus.UNAUTHORIZED:
            raise KeyError('<PRACTICUM_TOKEN> указан неверно')
        if api_answer.status_code != HTTPStatus.OK:
            raise Exception(
                f'API недоступен, код ошибки: {api_answer.status_code}'
            )
        return api_answer.json()
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        raise


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Oтвет API не является словарём')

    homeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if not (homeworks and current_date):
        raise MyCustomError(
            'Нет данных по ключам <homeworks> или <current_date>'
        )

    if isinstance(homeworks[0], list):
        logging.error('ДЗ приходят в виде списка')
        raise MyCustomError('ДЗ приходят в виде списка')
    else:
        return homeworks


def parse_status(homework):
    """Извлекает из запроса к API статус о последней домашней работе."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except MyCustomError:
        raise MyCustomError('Недокументированный статус домашней работы')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens_status = all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])
    if not TELEGRAM_TOKEN or not PRACTICUM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    else:
        return tokens_status


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler('my_logging.log', 'w', encoding='utf8'),
            logging.StreamHandler(sys.stdout),
        ],
        format=('%(asctime)s - '
                '%(levelname)s - '
                '%(message)s - '
                '%(name)s - '
                '%(filename)s - '
                '%(funcName)s - '
                '%(lineno)s'),
    )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    if check_tokens() is True:
        logging.info('Все токены доступны')
    else:
        logging.critical('Нет нужных токенов')
        send_message(bot, 'Нет нужных токенов')
        raise KeyError('Нет нужных токенов')

    from_date = 1638349200
    current_timestamp = int(time.time() - from_date)

    last_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            if last_message != message:
                send_message(bot, message)
            else:
                logging.debug('Статус не изменился')
            last_message = message

            date_updated = (
                homework[0].
                get('date_updated').
                replace('T', ' ').
                replace('Z', '')
            )
            date_updated_datetime = (
                datetime.datetime.fromisoformat(date_updated)
            )
            current_timestamp = int(date_updated_datetime.timestamp())

        except MyCustomError as error:
            message = f'Сбой в работе программы: {error}'
            logging.debug(message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.critical(message)
            if message != last_message:
                send_message(bot, message)
                last_message = message

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

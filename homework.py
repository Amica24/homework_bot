import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

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

prev_report = ''


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    global prev_report
    if prev_report != message:
        try:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
        except telegram.error.BadRequest as error:
            logger.error(f'Cбой при отправке сообщения в Telegram: {error}')
        else:
            prev_report = message
    return prev_report


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        message = (
            f'Сбой в работе программы: Эндпоинт '
            f'https://practicum.yandex.ru/api/user_api/homework_statuses/111'
            f'недоступен. Код ответа API: {response.status_code}'
        )
        logger.error(message)
        raise Exception(f'Код ответа API: {response.status_code}')
    else:
        return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response['homeworks']) is not list:
        message = 'Отсутствие ожидаемого типа данных в ответе API'
        logger.error(message)
        raise TypeError('Отсутствие ожидаемого типа данных в ответе API')
    elif 'homeworks' not in response:
        message = 'Отсутствие ожидаемого ключа homeworks в ответе API'
        logger.error(message)
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    elif 'current_date' not in response:
        message = 'Отсутствие ожидаемого ключа current_date в ответе API'
        logger.error(message)
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    else:
        logger.info('Ответ API корректен')
        return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        message = (
            f'Недокументированный статус домашней работы {homework_status},'
            f'обнаруженный в ответе API'
        )
        logger.error(message)
        raise KeyError(f'Неизвестный статус работы {homework_status}')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            if not check_tokens():
                message = (
                    'Отсутствие обязательных переменных окружения.'
                    'Программа принудительно остановлена.'
                )
                logger.critical(message)
                send_message(bot, message)
                raise SystemExit()
            response = get_api_answer(current_timestamp)
            try:
                homework = check_response(response)[0]
            except IndexError:
                logger.debug('Статус задания не обновлён.')
            else:
                message = parse_status(homework)
                send_message(bot, message)
                logger.info(f'Бот отправил сообщение {message}')
                current_timestamp = response.get('current_date')
            finally:
                time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logger.info('Программа работает без ошибок')


if __name__ == '__main__':
    main()

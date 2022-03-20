import logging
import sys
import time
from http import HTTPStatus

from exceptions import HttpStatusNotOK, EmptyAnswer
import requests
import telegram
from constants import (
    PRACTICUM_TOKEN, TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID, RETRY_TIME,
    ENDPOINT, HEADERS
)


# Логгер получется перенести в main и программа работает,
# но валятся тесты pytest
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# prev_report = ''


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    # global prev_report
    # if prev_report != message:
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except telegram.error.TelegramError as error:
        logger.error(f'Cбой при отправке сообщения в Telegram: {error}')
        # else:
        #     prev_report = message
    # return prev_report


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        message = (
            f'Сбой в работе программы: Эндпоинт {response.url}'
            f'недоступен. Код ответа API: {response.status_code}'
        )
        logger.error(message)
        raise HttpStatusNotOK(f'Код ответа API: {response.status_code}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response['homeworks'], list):
        message = 'Отсутствие ожидаемого типа данных в ответе API'
        logger.error(message)
        raise TypeError('Отсутствие ожидаемого типа данных в ответе API')
    elif not response:
        message = 'Отсутствие ожидаемого ключа в ответе API'
        logger.error(message)
        raise EmptyAnswer('Отсутствие ожидаемых ключей в ответе API')
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
# При использовании ValueError вместо KeyError валится тест


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_report = ''
    while True:
        try:
            if not check_tokens():
                message = (
                    'Отсутствие обязательных переменных окружения.'
                    'Программа принудительно остановлена.'
                )
                logger.critical(message)
                if prev_report != message:
                    send_message(bot, message)
                    prev_report = message
                sys.exit()
            response = get_api_answer(current_timestamp)
            try:
                homework = check_response(response)[0]
            except IndexError:
                logger.debug('Статус задания не обновлён.')
            else:
                message = parse_status(homework)
                if prev_report != message:
                    send_message(bot, message)
                    prev_report = message
                logger.info(f'Бот отправил сообщение {message}')
                current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if prev_report != message:
                send_message(bot, message)
                prev_report = message
        else:
            logger.info('Программа работает без ошибок')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

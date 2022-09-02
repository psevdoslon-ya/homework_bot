import os
import logging
import requests
import telegram
import time
import sys
import exceptions

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except exceptions.SendMessageFailure:
        raise exceptions.SendMessageFailure('Ошибка при отправке сообщения!')


def get_api_answer(current_timestamp):
    """Запрос к API сервису Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.HttpStatusOkError('Api недоступен')
        return response.json()
    except exceptions.GetApiStatusError as error:
        raise exceptions.GetApiStatusError(
            f'Ошибка при запросе к основному API: {error}'
        )


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response['homeworks'], list):
        raise TypeError('Ответ API не является списком!')
    if response['homeworks'] == []:
        raise IndexError('Список домашних работ пуст!')
    return response['homeworks']


def parse_status(homework):
    """Извлекаем из словаря статус проверки работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError as error:
        raise KeyError(f'Возникла ошибка {error} при запросе.')


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logging.debug('Бот запущен')
    if not check_tokens():
        message = 'Отсутствуют обязательные переменные окружения!'
        logging.critical(message)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    main()

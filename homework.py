# from asyncio.log import logger
import os
import logging
import requests
import telegram
import time
import sys

from dotenv import load_dotenv

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


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)


handler = logging.StreamHandler(stream=sys.stdout)


def send_message(bot, message) -> None:
    """Отправка сообщения в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Запрос к API сервису Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            logging.error('Api недоступен')
            raise Exception('Api недоступен')
        return response.json()
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        raise Exception(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверка ответа API на корректность."""
    if isinstance(response['homeworks'], list):
        if len(response['homeworks']) == 0:
            logging.error('Список домашних работ пуст!')
            raise IndexError('Список домашних работ пуст!')
        else:
            return response['homeworks']
    else:
        logging.error(Exception)
        raise Exception


def parse_status(homework):
    """Извлекаем из словаря статус проверки работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except TypeError as error:
        logging.error(f'Возникла ошибка {error} при запросе.')


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    logging.debug('Бот запущен')
    if not check_tokens():
        message = ('Отсутствуют обязательные переменные окружения!')
        logging.critical(message)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_status = None
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            new_status = homework[0]['status']
            if new_status != current_status:
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logging.INFO('Статус не изменился!')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

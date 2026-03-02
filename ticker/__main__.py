import asyncio
from os import getenv
from time import sleep
from datetime import datetime
from logging import INFO, basicConfig, getLogger

from requests import get
from bs4 import BeautifulSoup
from click import group, argument, option
from telegram.ext import Application, ApplicationBuilder


INTERVAL = 30  # seconds
TIMEOUT = 300  # seconds

TG_BOT_TOKEN = getenv('TG_BOT_TOKEN')
TG_CHAT_ID = int(getenv('TG_CHAT_ID'))

URL = 'https://doctrinaetnobiles.ru/lectures/{label}/'

logger = getLogger(__name__)
basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=INFO
)


@group()
def main():
    pass


def send_message(app: Application, message: str):
    async def send_message_async():
        await app.bot.sendMessage(TG_CHAT_ID, message)

    asyncio.run(send_message_async())


def now():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')


@main.command()
@argument('label', type = str)
@option('--interval', '-t', type = int, default = INTERVAL)
def track(label: str, interval: int):
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    url = URL.format(label = label)

    while True:
        try:
            response = get(url, timeout=TIMEOUT)
        except Exception as e:
            send_message(app, f'Failed to load page ({e})\n\n{url}')
            break

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')

            book_button = soup.find('p', class_='afdutton')

            if book_button is None:
                logger.info('The tickets for event %s are not available yet. Waiting for %d seconds before checking again...', label, interval)
                sleep(interval)
                continue

            send_message(app, f'The tickets are released!\n\n{url}')
            break
        else:
            send_message(app, f'Unexpected response status code ({response.status_code})\n\n{url}')
            break


if __name__ == '__main__':
    main()

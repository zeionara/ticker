from time import sleep
from datetime import datetime
from os import getenv
import asyncio

from click import group, argument, option

from requests import get, post
from telegram.ext import Application, ApplicationBuilder


INTERVAL = 20  # seconds

TG_BOT_TOKEN = getenv('TG_BOT_TOKEN')
TG_CHAT_ID = int(getenv('TG_CHAT_ID'))

URL = 'https://tickets.hermitagemuseum.org/event/{hash_id}'


@group()
def main():
    pass


def notify(app: Application, hash_id: str):
    async def send_message():
        await app.bot.sendMessage(TG_CHAT_ID, 'The tickets are released!\n\n' + URL.format(hash_id = hash_id))

    asyncio.run(send_message())


def now():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')


@main.command()
@argument('url', type = str, default = 'https://tickets.hermitagemuseum.org/api/afisha')
@option('--insecure', '-i', is_flag = True)
@option('--interval', '-t', type = int, default = INTERVAL)
def track(url: str, insecure: bool, interval: int):
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    while True:
        page = get(url, verify = not insecure)

        # response = loads(page.text.encode('latin-1').decode('unicode-escape'))
        response = page.json()

        for action in response['response']['action']:
            description = action.get('descript_ru')

            if description is not None and description.startswith('Бесплатный'):
                hash_id = action.get('hash_id')

                page = post('https://tickets.hermitagemuseum.org/api/no-scheme', json = {'hash': hash_id}, verify = not insecure)

                response = page.json()

                if response['response']['action']:
                    notify(app, hash_id)

                    print(f'{now()} The tickets are available @ {URL.format(hash_id = hash_id)}. Notification has been sent.')
                    return
                else:
                    print(f'{now()} The tickets are not available @ {URL.format(hash_id = hash_id)}. Retrying in {interval} seconds.')
                    # print(response)
                    # print()

                    sleep(interval)
                    break


if __name__ == '__main__':
    main()

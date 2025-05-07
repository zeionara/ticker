from time import sleep
from datetime import datetime, timedelta
from os import getenv
import asyncio
from json import loads
import pandas as pd

from click import group, argument, option

from requests import get, post
from telegram.ext import Application, ApplicationBuilder


INTERVAL = 20  # seconds

TG_BOT_TOKEN = getenv('TG_BOT_TOKEN')
TG_CHAT_ID = None if getenv('TG_CHAT_ID') is None else int(getenv('TG_CHAT_ID'))

URL = 'https://tickets.hermitagemuseum.org/event/{hash_id}'

DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'


@group()
def main():
    pass


def notify(app: Application, hash_id: str):
    async def send_message():
        await app.bot.sendMessage(TG_CHAT_ID, 'The tickets are released!\n\n' + URL.format(hash_id = hash_id))

    asyncio.run(send_message())


def now():
    return datetime.now().strftime(DATETIME_FORMAT)


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

                print(response)

                # if response['response']['action']:
                #     notify(app, hash_id)

                #     print(f'{now()} The tickets are available @ {URL.format(hash_id = hash_id)}. Notification has been sent.')
                #     return
                # else:
                #     print(f'{now()} The tickets are not available @ {URL.format(hash_id = hash_id)}. Retrying in {interval} seconds.')
                #     print(response)
                #     # print()

                #     sleep(interval)
                #     break

        print()
        sleep(interval)


@main.command()
@argument('path', type = str, default = 'log.jsonl')
@option('--end-time', '-e', type = str, default = '07-05-2025 12:48:30')
@option('--interval', '-t', type = int, default = INTERVAL)
def parse_logs(path: str, end_time: str, interval: int):
    measurement_time = datetime.strptime(end_time, DATETIME_FORMAT)

    with open(path, 'r', encoding = 'utf-8') as file:
        lines = [line[:-1] for line in file.readlines()]

        n_events = 0

        for line in lines:
            if line:
                n_events += 1
                continue

            break

        events = [[] for _ in range(n_events)]

        i = 0

        for line in lines:
            if line:
                events[i % n_events].append(eval(line))
                i += 1

    dfs = []

    for i in reversed(range(len(events[0]))):  # for each measurement
        series = []
        columns = []

        for j, entries in enumerate(events):
            if j == 3:
                continue

            for day in entries[i]['response']['calendar']:
                date = day['day'].replace('.', '-')

                timetags = []
                quantities = []

                for time in day['_time']:
                    timetags.append(datetime.strptime(f'{date} {time["time"]}:00', DATETIME_FORMAT))
                    quantities.append(int(time['quantity']))

                columns.append(entries[i]['response']['action']['action_ru'].split('.')[-1].strip().replace('  ', ' '))

                series.append(pd.Series(quantities, index = timetags))

        df_data = {
            column: values
            for values, column in zip(series, columns)
        }
        df_data['Время посещения'] = series[0].index
        df_data['Время измерения'] = measurement_time
        # df_index = pd.MultiIndex.from_tuples([(timetag, measurement_time) for timetag in series[0].index], names = ('Время сеанса', 'Время измерения'))

        df = pd.DataFrame(df_data).set_index(['Время посещения', 'Время измерения'])
        measurement_time -= timedelta(seconds = interval)

        dfs.append(df)

    df = pd.concat(reversed(dfs))
    df.to_csv('log.csv')


if __name__ == '__main__':
    main()

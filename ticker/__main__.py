from time import sleep
from datetime import datetime, timedelta
from os import getenv
import asyncio

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

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
@argument('path', type = str, default = 'assets/log.jsonl')
@argument('log', type = str, default = 'assets/log.csv')
@option('--end-time', '-e', type = str, default = '07-05-2025 12:48:30')
@option('--interval', '-t', type = int, default = INTERVAL)
def parse_logs(path: str, log: str, end_time: str, interval: int):
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

    df = df.copy()

    df['Вход со стороны Иорданской лестницы'] = 100
    df['Вход со стороны Церковной лестницы'] = 100
    df['Вход со стороны Шуваловского проезда'] = 100
    df['Входной билет в Главный Штаб'] = 100

    df['Время измерения'] = datetime(2025, 5, 7, 12, 0, 0)
    df['Время посещения'] = series[0].index

    df = df.set_index(['Время посещения', 'Время измерения'])

    dfs.append(df)

    df = pd.concat(reversed(dfs))
    df.to_csv(log)


@main.command()
@argument('path', type = str, default = 'assets/log.csv')
@argument('plot', type = str, default = 'assets/plot.png')
def visualize(path: str, plot: str):
    df = pd.read_csv(
        path,
        parse_dates=['Время посещения', 'Время измерения'],
        dayfirst=False  # Adjust if dates are in day-month format
    )

    # Get unique visit times
    visit_times = df['Время посещения'].unique()

    # Columns to visualize
    columns = [
        'Вход со стороны Иорданской лестницы',
        'Вход со стороны Церковной лестницы',
        'Вход со стороны Шуваловского проезда',
        'Входной билет в Главный Штаб'
    ]

    # Create figure with subplots
    fig, axs = plt.subplots(2, 2, figsize = (30, 20))
    plt.subplots_adjust(hspace = 0.5)

    axs = [item for ax in axs for item in ax]

    # Plot each column in separate subplot
    for idx, col in enumerate(columns):
        ax = axs[idx]

        # Plot lines for each visit time
        for vt in visit_times:
            subset = df[df['Время посещения'] == vt]
            ax.plot(
                subset['Время измерения'],
                subset[col],
                # marker='o',
                linestyle='-',
                label = vt.strftime(DATETIME_FORMAT)
            )

        # Format subplot
        ax.set_title(col, fontsize=12)
        ax.set_xlabel('Время измерения', fontsize=10)
        ax.set_ylabel('Количество билетов', fontsize=10)
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S\n%d-%m-%Y'))
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

        # Add legend with smaller font
        ax.legend(
            bbox_to_anchor=(1.05, 1),
            loc='upper left',
            fontsize=6,
            title='Время посещения',
            title_fontsize=8
        )

    # Save and close
    plt.savefig(plot, bbox_inches='tight', dpi=150)
    plt.close()


if __name__ == '__main__':
    main()

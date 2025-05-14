from time import sleep

from click import group, argument, option

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


INTERVAL = 1  # seconds
MAX_INTERVAL = 3600  # seconds
BASE_URL = 'https://ticketscloud.com/v1/widgets/common?{params}'


@group()
def main():
    pass


@main.command()
@argument('params', type = str, default = 'event=6823b1231b7a37f588951e7e&token=eyJhbGciOiJIUzI1NiIsImlzcyI6InRpY2tldHNjbG91ZC5ydSIsInR5cCI6IkpXVCJ9.eyJwIjoiNjVlNzEyZjBhZTRjNWUyOGNmNGZkZDNhIn0.9WpViaffsyOmzAOTYgCotINkLlFSMgSGB8dI7uFzU3w&lang=ru')
@option('--interval', '-t', type = int, default = INTERVAL)
def track(params: str, interval: int):
    driver = webdriver.Chrome()
    ordered = False

    while True:
        driver.get(BASE_URL.format(params = params))

        n_attempts = 2

        selected = False

        while True:
            try:
                # buy_ticket_button = driver.find_elements(By.CLASS_NAME, "//*[contains(text(), 'Купить Билет')]/ancestor::a")[-1]
                input_counter_ups = driver.find_elements(By.CLASS_NAME, "input-counter_up")
            except NoSuchElementException:
                print('No such element.')

                if n_attempts > 0:
                    n_attempts -= 1
                    sleep(0.2)
                else:
                    break
            else:
                if len(input_counter_ups) < 1:
                    print('No such element.')

                    if n_attempts > 0:
                        n_attempts -= 1
                        sleep(0.2)
                        continue
                    else:
                        break

                input_counter_up = input_counter_ups[0]
                input_counter_up.click()

                selected = True

                break

        if not selected:
            sleep(interval)
            print('Reloading...')
            continue

        n_attempts = 2

        while True:
            try:
                submits = driver.find_elements(By.CLASS_NAME, "ticket-list__submit-btn")
            except NoSuchElementException:
                print('No such element.')

                if n_attempts > 0:
                    n_attempts -= 1
                    sleep(0.2)
                else:
                    break
            else:
                if len(submits) < 1:
                    print('No such element.')

                    if n_attempts > 0:
                        n_attempts -= 1
                        sleep(0.2)
                        continue
                    else:
                        break

                submit = submits[0]
                submit.click()

                ordered = True

                break

        if ordered:
            break

        sleep(interval)

    sleep(MAX_INTERVAL)


if __name__ == '__main__':
    main()

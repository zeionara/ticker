from time import sleep

from click import group, argument, option

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


INTERVAL = 1  # number of seconds between selecting the ticket type and creating an order
INDEX = 2  # index of option to select
MAX_INTERVAL = 3600  # number of seconds to wait for at the end of script for letting the user to make the purchase
N_ATTEMPTS = 2  # number of attempts to find counter ups on the page before refreshing the site
ATTEMPT_INTERVAL = 0.2  # number of seconds between attempts to parse elements from a web page
BASE_URL = 'https://ticketscloud.com/v1/widgets/common?{params}'


@group()
def main():
    pass


@main.command()
@argument('params', type = str, default = 'event=68b78e2bd3223a746990bafc&token=eyJhbGciOiJIUzI1NiIsImlzcyI6InRpY2tldHNjbG91ZC5ydSIsInR5cCI6IkpXVCJ9.eyJwIjoiNjVlNzEyZjBhZTRjNWUyOGNmNGZkZDNhIn0.9WpViaffsyOmzAOTYgCotINkLlFSMgSGB8dI7uFzU3w')
@option('--interval', '-t', type = int, default = INTERVAL)
@option('--index', '-i', type = int, default = INDEX)
@option('--attempts', '-a', type = int, default = N_ATTEMPTS)
@option('--attempt-interval', '-r', type = float, default = ATTEMPT_INTERVAL)
def track(params: str, interval: int, index: int, attempts: int, attempt_interval: float):
    driver = webdriver.Chrome()
    ordered = False

    assert index > 0, 'Index must be greater than zero'

    while True:
        driver.get(BASE_URL.format(params = params))

        n_attempts = attempts

        selected = False

        while True:  # Find input counter up button
            try:
                # buy_ticket_button = driver.find_elements(By.CLASS_NAME, "//*[contains(text(), 'Купить Билет')]/ancestor::a")[-1]
                input_counter_ups = driver.find_elements(By.CLASS_NAME, "input-counter_up")
            except NoSuchElementException:
                print(f'No such element (counter up, error). Attempt {N_ATTEMPTS - n_attempts + 1}')

                if n_attempts > 1:
                    n_attempts -= 1
                    sleep(attempt_interval)
                else:
                    break
            else:
                if len(input_counter_ups) < 1:
                    print(f'No such element (counter up, empty list). Attempt {N_ATTEMPTS - n_attempts + 1}')

                    if n_attempts > 1:
                        n_attempts -= 1
                        sleep(attempt_interval)
                        continue
                    break

                input_counter_up = input_counter_ups[min(index, len(input_counter_ups)) - 1]
                input_counter_up.click()

                selected = True

                break

        if not selected:
            sleep(interval)
            print('Reloading...')
            continue

        n_attempts = attempts

        while True:
            try:
                submits = driver.find_elements(By.CLASS_NAME, "ticket-list__submit-btn")
            except NoSuchElementException:
                print('No such element.')

                if n_attempts > 1:
                    n_attempts -= 1
                    sleep(attempt_interval)
                else:
                    break
            else:
                if len(submits) < 1:
                    print('No such element.')

                    if n_attempts > 1:
                        n_attempts -= 1
                        sleep(attempt_interval)
                        continue
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

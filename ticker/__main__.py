from time import sleep

from click import group, argument, option

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.action_chains import ActionChains


INTERVAL = 20  # seconds
# BASE_URL = 'https://ticketscloud.com/v1/widgets/common?'


@group()
def main():
    pass


@main.command()
@argument('url', type = str, default = 'https://monasterio.moscow/goodbyearma')
@option('--interval', '-t', type = int, default = INTERVAL)
def track(url: str, interval: int):
    driver = webdriver.Chrome()
    # ac = ActionChains(driver)
    wait = WebDriverWait(driver, timeout = 2)

    while True:
        driver.get(url)

        try:
            buy_ticket_button = driver.find_elements(By.XPATH, "//*[contains(text(), 'Купить Билет')]/ancestor::a")[-1]
        except NoSuchElementException:
            print('No such element.')
        else:
            wait.until(lambda _: buy_ticket_button.is_displayed())

            buy_ticket_button.click()
            # ac.move_to_element(buy_ticket_button).perform()
            # sleep(1)
            # ac.click(buy_ticket_button).perform()

        sleep(interval)


if __name__ == '__main__':
    main()

import json
from datetime import datetime
from parser import ScheduleParser

import requests
from selenium.webdriver.common.by import By

from base import WebBot
from conf import settings
from logger import logger

if __name__ == "__main__":
    options = {
        "download.default_directory": str(settings.PATH_SAVE_FILES),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    bot = WebBot(
        options=[
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
        experimental_options=options,
    )

    logger.info(f"Start bot at {datetime.now()} \n")

    bot.open_page(
        url="https://auth-dziekanat.wst.com.pl/Account/Login?ReturnUrl=%2F",
        time_sleep_sec=2,
    )

    bot.click_button(by=By.CLASS_NAME, value="social-media", time_sleep_sec=2)  # Redirect to login page

    bot.add_input(by=By.ID, value="i0116", text=settings.EMAIL_ADDRESS)  # Enter e-mail
    bot.click_button(by=By.ID, value="idSIButton9", time_sleep_sec=2)  # Click and redirect to enter password

    bot.add_input(by=By.ID, value="i0118", text=settings.PASSWORD)  # Enter password
    bot.click_button(by=By.ID, value="idSIButton9", time_sleep_sec=3)  # Redirect to YES or NO modal

    logger.info("Logged.")

    if bot.find_element(by=By.ID, value="cancelLink", time_sleep_sec=1):
        bot.click_button(by=By.ID, value="cancelLink", time_sleep_sec=1)

    if bot.find_element(by=By.ID, value="idSIButton9", time_sleep_sec=1):
        bot.click_button(by=By.ID, value="idSIButton9", time_sleep_sec=3)

    if bot.find_element(by=By.CSS_SELECTOR, value='div[aria-label*="Sign in with"]', time_sleep_sec=1):
        bot.click_button(by=By.CSS_SELECTOR, value='div[aria-label*="Sign in with"]', time_sleep_sec=2)

    # bot.click_button(
    #     by=By.ID, value="idSIButton9", time_sleep_sec=4
    # )  # Redirect to nDziekenat

    bot.click_button(by=By.CLASS_NAME, value="btn-primary", time_sleep_sec=6)  # Click "Return to nDziekanat"

    bot.open_page(url="https://dziekanat.wst.com.pl/pl/repozytorium-plikow", time_sleep_sec=5)  # Open page

    bot.add_input(by=By.ID, value="nazwa-input", text=f"{settings.FILE_NAME.lower()}")
    bot.click_button(by=By.XPATH, value='//button[text()="Szukaj"]', time_sleep_sec=1)

    bot.click_button(
        by=By.XPATH,
        value=f'//button[contains(text(), "{settings.FILE_NAME}")]',
        time_sleep_sec=5,
    )
    logger.info("Saved file.")

    bot.close_page()

    file = open(
        f"{str(settings.PATH_SAVE_FILES)}/{settings.FILE_NAME_PATH}.xls",
        "rb",
    )

    parsed_dict_file = ScheduleParser(schedule_file_name=settings.FILE_NAME_PATH).parse()

    data = json.dumps(parsed_dict_file, indent=4, ensure_ascii=False)

    files = {
        "file": file,
    }

    response = requests.post(
        f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/schedules/files",
        files=files,
    )

    logger.info(f"Response: {response.json()}")

    if response.json()["is_email_sent"] or settings.ALWAYS_UPDATE_SCHEDULES:
        response = requests.post(
            f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/schedules",
            data=data,
        )

    logger.info(f"Sent file to API. Status: {response.status_code}")

    logger.info(f"Finish bot at {datetime.now()} \n")

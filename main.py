import hashlib
import os
from datetime import datetime

import requests
from selenium.webdriver.common.by import By

from base import WebBot
from conf import settings

if __name__ == "__main__":
    options = {
        "download.default_directory": settings.PATH_SAVE_FILES.__str__(),
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

    print(f"Start bot at {datetime.now()} \n")

    bot.open_page(
        url="https://auth-dziekanat.wst.com.pl/Account/Login?ReturnUrl=%2F",
        time_sleep_sec=2,
    )

    bot.click_button(
        by=By.CLASS_NAME, value="social-media", time_sleep_sec=2
    )  # Redirect to login page

    bot.add_input(by=By.ID, value="i0116", text=settings.EMAIL_ADDRESS)  # Enter e-mail
    bot.click_button(
        by=By.ID, value="idSIButton9", time_sleep_sec=2
    )  # Click and redirect to enter password

    bot.add_input(by=By.ID, value="i0118", text=settings.PASSWORD)  # Enter password
    bot.click_button(
        by=By.ID, value="idSIButton9", time_sleep_sec=3
    )  # Redirect to YES or NO modal

    print("Logged.")

    bot.click_button(
        by=By.ID, value="idSIButton9", time_sleep_sec=4
    )  # Redirect to nDziekenat

    bot.click_button(
        by=By.CLASS_NAME, value="btn-primary", time_sleep_sec=6
    )  # Click "Return to nDziekanat"

    bot.open_page(
        url="https://dziekanat.wst.com.pl/pl/repozytorium-plikow", time_sleep_sec=5
    )  # Open page

    bot.add_input(by=By.ID, value="nazwa-input", text=f"{settings.FILE_NAME.lower()}")
    bot.click_button(by=By.XPATH, value='//button[text()="Szukaj"]', time_sleep_sec=1)

    bot.click_button(
        by=By.XPATH,
        value=f'//button[contains(text(), "{settings.FILE_NAME}")]',
        time_sleep_sec=5,
    )
    print("Saved file.")

    bot.close_page()

    file = open(
        f"/home/michal/workspaces/AScheduleApp/web-bot/media_files/{settings.FILE_NAME_PATH}.xls",
        "rb",
    )
    file_binary_content = file.read()
    md5_file = hashlib.md5(file_binary_content).hexdigest()
    print(f"MD5: {md5_file}")
    print("Sent file to API.")
    file.seek(0)
    files = {"file": file}
    requests.post("http://127.0.0.1:8000/schedule", files=files)
    file.close()
    if os.path.exists(f"{settings.PATH_SAVE_FILES / settings.FILE_NAME_PATH}.xls"):
        os.remove(f"{settings.PATH_SAVE_FILES / settings.FILE_NAME_PATH}.xls")
    print(f"Finish bot at {datetime.now()} \n")

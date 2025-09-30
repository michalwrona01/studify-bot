import time
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class WebBot:
    def __init__(self, options: List[str] = (), experimental_options: Optional[dict] = ()):
        service = Service()
        self.options = webdriver.ChromeOptions()
        for option in options:
            self.options.add_argument(option)
        if experimental_options:
            self.options.add_experimental_option(name="prefs", value=experimental_options)
        self.browser = webdriver.Chrome(service=service, options=self.options)

    def open_page(self, url: str, time_sleep_sec: int = 0):
        self.browser.get(url=url)
        time.sleep(time_sleep_sec)

    def close_page(self):
        self.browser.close()

    def add_input(self, by: By, value: str, text: str, time_sleep_sec: int = 0):
        field = self.browser.find_element(by=by, value=value)
        field.send_keys(text)
        time.sleep(time_sleep_sec)

    def click_button(self, by: By, value: str, time_sleep_sec: int = 0):
        button = self.browser.find_element(by=by, value=value)
        button.click()
        time.sleep(time_sleep_sec)

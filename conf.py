from pathlib import Path

from vault.vault_settings import *

BASE_DIR = Path(__file__).resolve().parent


class Settings:
    def __init__(self):
        self.EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        self.PASSWORD = os.getenv("PASSWORD")
        self.PATH_SAVE_FILES = os.getenv("PATH_SAVE_FILES", BASE_DIR / "mediafiles")
        self.THRESHOLD_TIME_MIN = int(os.getenv("THRESHOLD_TIME", 5)) * 60
        self.FILE_NAME = os.getenv("FILE_NAME")
        self.FILE_NAME_PATH = os.getenv("FILE_NAME_PATH")


settings = Settings()

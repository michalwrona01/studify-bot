import os
import re
from copy import copy
from pathlib import Path
from typing import Dict, List

import pandas as pd
from bs4 import BeautifulSoup

from conf import settings
import subprocess

mapped_columns = {
    "DATA": "date",
    "Dzień tyg.": "day_of_week",
    "GRUPA": "group",
    "SEKCJA": "section",
    "TRYB": "mode",
}


class ScheduleParser:
    def __init__(self, *, schedule_file_name: Path):
        self.schedule_file_name = schedule_file_name
        self.schedule_file_path_xls = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xls")
        self.schedule_file_path_xlsx = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xlsx")
        self.schedule_file_path_html = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.html")

    def parse(self) -> List[Dict]:
        try:
            converted = self._convert_to_dict()
            normalized = self._normalize(converted)
        except Exception as exc:
            raise exc from exc
        finally:
            self._clean_up()
        return normalized

    def _convert_to_dict(self):
        x2x = XLS2XLSX(self.schedule_file_path_xls)
        x2x.to_xlsx(self.schedule_file_path_xlsx)

        command = [
            "soffice",
            "--headless",
            "--convert-to",
            "html",
            self.schedule_file_path_xlsx,
            "--outdir",
            settings.PATH_SAVE_FILES,
        ]

        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
        print(result.stdout)

        try:
            with open(self.schedule_file_path_html, "r", encoding="utf-8") as file:
                html_content = file.read()
        except FileNotFoundError:
            print(f"Błąd: Plik '{self.schedule_file_path_html}' nie został znaleziony.")
            exit()

        soup = BeautifulSoup(html_content, "html.parser")

        for s_tag in soup.find_all("s"):
            font_tag = s_tag.find("font")
            if font_tag and font_tag.string:
                original_text = font_tag.string.strip()
                if not original_text.startswith("[ODWOŁANE] - "):
                    new_text = f"[ODWOŁANE] - {original_text}"
                    font_tag.string.replace_with(new_text)

        with open(self.schedule_file_path_html, "w", encoding="utf-8") as file:
            file.write(str(soup))

        df = pd.read_html(self.schedule_file_path_html, header=3)
        df = df[0]

        unnamed_columns = [column for column in df.columns if column.startswith("Unnamed")]
        df = df.drop(columns=unnamed_columns)

        df = df.fillna("")

        df = df[df["SEKCJA"] != ""]

        df["DATA"] = pd.to_datetime(df["DATA"], format="%m/%d/%Y").dt.date

        df["DATA"] = df["DATA"].apply(lambda x: x.isoformat())

        return df.to_dict(orient="records")

    def _normalize(self, data: List[Dict]):
        normalized_data = []

        for day in data:
            normalize_day = copy(day)
            normalize_day["hours"] = {}
            for key in day.keys():
                if re.match(r"(\d{2}:\d{2})-(\d{2}:\d{2})", str(key)):
                    if day[key]:
                        normalize_day["hours"][key] = day[key]
                    normalize_day.pop(key)

            normalize_day = {mapped_columns.get(k, k): v for k, v in normalize_day.items()}

            normalized_data.append(normalize_day)

        return normalized_data

    def _clean_up(self):
        if os.path.exists(self.schedule_file_path_xls):
            os.remove(self.schedule_file_path_xls)

        if os.path.exists(self.schedule_file_path_xlsx):
            os.remove(self.schedule_file_path_xlsx)

        if os.path.exists(self.schedule_file_path_html):
            os.remove(self.schedule_file_path_html)

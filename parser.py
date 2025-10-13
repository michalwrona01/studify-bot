import os
import re
import subprocess
from copy import copy
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

import pandas as pd
from bs4 import BeautifulSoup
from xls2xlsx import XLS2XLSX

from conf import settings
from logger import logger

mapped_columns = {
    "DATA": "date",
    "Dzień tyg.": "day_of_week",
    "GRUPA": "group",
    "SEKCJA": "section",
    "TRYB": "mode",
}

ADDRESSES = {
    "Chirurgia - Przewód pokarmowy": {
        "address": "Zagłębiowskie Centrum Onkologii Szpital Specjalistyczny im. Sz. Starkiewicza w Dąbrowie Górniczej, ul. Szpitalna 13",
        "lat": 50.32062360179699,
        "lng": 19.178391961037644,
    },
    "Chirurgia onkologiczna": {
        "address": "Zagłębiowskie Centrum Onkologii Szpital Specjalistyczny im. Sz. Starkiewicza w Dąbrowie Górniczej, ul. Szpitalna 13",
        "lat": 50.32062360179699,
        "lng": 19.178391961037644,
    },
    "Choroby wewnętrzne - Gastrologia": {
        "address": "H-T. Centrum Medyczne Tychy, al. Bielska 105",
        "lat": 50.115089834344694,
        "lng": 18.982719477121265,
    },
    "Choroby wewnętrzne - Nefrologia": {
        "address": "Wojewódzki Szpital Specjalistyczny nr 5 im. Św. Barbary w Sosnowcu, Plac medyków 1",
        "lat": 50.30456441269166,
        "lng": 19.123207362963445,
    },
    "Dermatologia i wenerologia": {
        "address": "Skin Laser Lubelscy, ul. Azaliowa 2, Bielsko-Biała",
        "lat": 49.79794559103984,
        "lng": 19.039727292868893,
    },
    "Kardiochirurgia": {
        "address": "Polsko-Amerykańskie Kliniki Serca w Bielsku-Białej, al. Armii Krajowej 101",
        "lat": 49.790420120276444,
        "lng": 19.040722061587246,
    },
    "Okulistyka": {
        "address": "Wojewódzki Szpital Specjalistyczny nr 5 im. Św. Barbary w Sosnowcu, Plac medyków 1",
        "lat": 50.30456397332421,
        "lng": 19.1232072434493,
    },
    "Onkologia": {
        "address": "Beskidzkie Centrum Onkologii w Bielsku-Białej, ul. Wyspiańskiego 21; Pawilon IV",
        "lat": 49.82311009704879,
        "lng": 19.035610117937317,
    },
    "Otorynolaryngologia": {
        "address": "Zagłębiowskie Centrum Onkologii Szpital Specjalistyczny im. Sz. Starkiewicza w Dąbrowie Górniczej, ul. Szpitalna 13",
        "lat": 50.320620958626364,
        "lng": 19.17839208199305,
    },
    "Pediatria - Hematologia": {
        "address": "Zespół Szpitali Miejskich w Chorzowie ul. Truchana 7",
        "lat": 50.29678654719145,
        "lng": 18.948361459799177,
    },
    "Pediatria - Laryngologia": {
        "address": "Zespół Szpitali Miejskich w Chorzowie ul. Truchana 7",
        "lat": 50.29678654719145,
        "lng": 18.948361459799177,
    },
}


def uid_gen() -> str:
    uid = str(uuid4())
    return f"{uid}@as.wronamichal.pl"


class ScheduleParser:
    def __init__(self, *, schedule_file_name: Path):
        self.schedule_file_name = schedule_file_name
        self.schedule_file_path_xls = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xls")
        self.schedule_file_path_xlsx = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xlsx")
        self.schedule_file_path_html = str(settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.html")

    def parse(self) -> List[Dict]:
        logger.info(f"Start parsing {self.schedule_file_name}")
        try:
            converted = self._convert_to_dict()
            logger.info(f"Converted {self.schedule_file_name}")
            normalized = self._normalize_hours(converted)
            logger.info(f"Normalization done")
        except Exception as exc:
            logger.error(f"Failed to convert {self.schedule_file_name}")
            raise exc from exc
        finally:
            logger.info(f"Finish parsing {self.schedule_file_name}")
            self._clean_up()

        return normalized

    @staticmethod
    def _convert_xlsx_to_html(*, xls_path: str, out_dir_path: str):
        logger.info(f"Converting {xls_path} to html")
        command = [
            "soffice",
            "--headless",
            "--convert-to",
            "html",
            xls_path,
            "--outdir",
            out_dir_path,
        ]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
        logger.info("Finish converting xls to html")

    @staticmethod
    def _mark_canceled_classes(*, html_path: str):
        try:
            with open(html_path, "r", encoding="utf-8") as file:
                html_content = file.read()
        except FileNotFoundError as exc:
            logger.error(f"File {html_path} not found")
            raise exc from exc

        soup = BeautifulSoup(html_content, "html.parser")

        for s_tag in soup.find_all("s"):
            font_tag = s_tag.find("font")
            if font_tag and font_tag.string:
                original_text = font_tag.string.strip()
                if not original_text.startswith("[ODWOŁANE] - "):
                    new_text = f"[ODWOŁANE] - {original_text}"
                    font_tag.string.replace_with(new_text)

        with open(html_path, "w", encoding="utf-8") as file:
            file.write(str(soup))

    @staticmethod
    def _convert_xls_to_xlsx(*, xls_path: str, xlsx_path: str):
        logger.info(f"Start converting xls to xlsx")
        x2x = XLS2XLSX(xls_path)
        x2x.to_xlsx(xlsx_path)
        logger.info(f"Finish converting xls to xlsx")

    def _convert_to_dict(self):
        self._convert_xls_to_xlsx(xls_path=self.schedule_file_path_xls, xlsx_path=self.schedule_file_path_xlsx)
        self._convert_xlsx_to_html(xls_path=self.schedule_file_path_xlsx, out_dir_path=settings.PATH_SAVE_FILES)
        self._mark_canceled_classes(html_path=self.schedule_file_path_html)

        df = pd.read_html(self.schedule_file_path_html, header=3)
        df = df[0]

        unnamed_columns = [column for column in df.columns if column.startswith("Unnamed")]
        df = df.drop(columns=unnamed_columns)

        df = df.fillna("")

        df = df[df["SEKCJA"] != ""]

        df["DATA"] = pd.to_datetime(df["DATA"], format="%m/%d/%Y").dt.date

        df["DATA"] = df["DATA"].apply(lambda x: x.isoformat())

        return df.to_dict(orient="records")

    @staticmethod
    def _normalize_hours(data: List[Dict]):
        normalized_data = []

        for day in data:
            normalize_day = copy(day)
            normalize_day["hours"] = {}
            for key in day.keys():
                if re.match(r"(\d{2}:\d{2})-(\d{2}:\d{2})", str(key)):
                    if day[key]:
                        for subject, location in ADDRESSES.items():
                            if subject in day[key] and "ONLINE" not in day[key]:
                                found_location = location
                                break
                        else:
                            found_location = {}

                        normalize_day["hours"][key] = {
                            "name": day[key],
                            "uid": uid_gen(),
                            "location": found_location.get("address"),
                            "lat": found_location.get("lat"),
                            "lng": found_location.get("lng"),
                        }
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

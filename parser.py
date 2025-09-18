import os
import re
from copy import copy
from pathlib import Path
from typing import Dict, List

import pandas as pd
from conf import settings
from xls2xlsx import XLS2XLSX
from xlsx2html import xlsx2html

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
        self.schedule_file_path_xls = str(
            settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xls"
        )
        self.schedule_file_path_xlsx = str(
            settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.xlsx"
        )
        self.schedule_file_path_html = str(
            settings.PATH_SAVE_FILES / f"{self.schedule_file_name}.html"
        )

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

        xlsx2html(
            self.schedule_file_path_xlsx, output=self.schedule_file_path_html, sheet=0
        )

        df = pd.read_html(self.schedule_file_path_html, header=3)
        df = df[0]

        unnamed_columns = [
            column for column in df.columns if column.startswith("Unnamed")
        ]
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

            normalize_day = {
                mapped_columns.get(k, k): v for k, v in normalize_day.items()
            }

            normalized_data.append(normalize_day)

        return normalized_data

    def _clean_up(self):
        if os.path.exists(self.schedule_file_path_xls):
            os.remove(self.schedule_file_path_xls)

        if os.path.exists(self.schedule_file_path_xlsx):
            os.remove(self.schedule_file_path_xlsx)

        if os.path.exists(self.schedule_file_path_html):
            os.remove(self.schedule_file_path_html)

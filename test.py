# import json
# import os
# from pathlib import Path
#
# import pandas as pd
# from xls2xlsx import XLS2XLSX
# from xlsx2html import xlsx2html
#
# pd.set_option("display.max_rows", None)  # Pokaż wszystkie wiersze
# pd.set_option("display.max_columns", None)  # Pokaż wszystkie kolumny
# pd.set_option("display.expand_frame_repr", False)  # Nie zawijaj kolumn
#
# filename_xls = "./Lekarski semestr 6.xls"
# filename_xlsx = "./Lekarski semestr 6.xlsx"
# file_name_html = "./Lekarski semestr 6.html"
# file_name_html_filtered = "./Lekarski semestr 6 filtered.html"
# file_name_json_filtered = "./Lekarski semestr 6 filtered.json"
# #
# BASE_DIR = Path(__file__).resolve().parent
#
# x2x = XLS2XLSX(filename_xls)
# x2x.to_xlsx(filename_xlsx)
#
# xlsx2html(filename_xlsx, output=file_name_html, sheet=1)
#
# if os.path.exists(filename_xlsx):
#     os.remove(filename_xlsx)
#
# df = pd.read_html(file_name_html, header=4)
# df = df[0]
#
# unnamed_columns = [column for column in df.columns if column.startswith("Unnamed")]
# df = df.drop(columns=unnamed_columns)
#
# df = df.fillna("")
#
# df["DATA"] = pd.to_datetime(df["DATA"], format="%m/%d/%Y")
# # today = pd.Timestamp.today().normalize()
# # date_delta_1_day = pd.Timedelta(days=1)
# #
# # df = df[df['DATA'] >= today - date_delta_1_day]
# df["DATA"] = df["DATA"].apply(lambda x: x.isoformat())
#
# # df.to_html(file_name_html_filtered, encoding="windows-1250")
# data_dict = df.to_dict(orient="records")
#
# file = open(file_name_json_filtered, "w", encoding="utf-8")
# file.write(json.dumps(data_dict, indent=4, ensure_ascii=False))
# file.close()
#
# print(df)


lista = [
    {
        "DATA": "2025-02-26T00:00:00",
        "Dzień tyg.": "środa",
        "GRUPA": "2A-5",
        "SEKCJA": 5,
        "TRYB": "ST",
        "08:00-08:45": "",
        "08:45-09:30": "",
        "09:30-10:15": "",
        "10:20-11:05": "",
        "11:05-11:50": "",
        "11:50-12:35": "",
        "12:40-13:25": "",
        "13:25-14:10": "",
        "14:10-14:55": "",
        "15:00-15:45": "",
        "15:45-16:30": "",
        "16:30-17:15": "Choroby wewnętrzne - Kardiologia prof. dr hab. Krzysztof Milewski wykład ONLINE, godz. 17:00-18:30",
        "17:20-18:05": "Choroby wewnętrzne - Kardiologia prof. dr hab. Krzysztof Milewski wykład ONLINE, godz. 17:00-18:30",
        "18:05-18:50": "Choroby wewnętrzne - Kardiologia prof. dr hab. Krzysztof Milewski wykład ONLINE, godz. 18:35-20:05",
        "18:50-19:35": "Choroby wewnętrzne - Kardiologia prof. dr hab. Krzysztof Milewski wykład ONLINE, godz. 18:35-20:05",
        "19:40-20:25": "",
        "20:25-21:15": "",
    }
]

import requests
import csv
import datetime
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Scraper for Abfallplus (= abfall.io) based services"
URL = "https://www.abfallplus.de"
TEST_CASES = OrderedDict(
    [
        (
            "Waldenbuch",
            {
                "key": "8215c62763967916979e0e8566b6172e",
                "kommune": 2999,
                "bezirk": None,
                "strasse": 1087,
                "abfallarten": [50, 53, 31, 299, 328, 325],
            },
        ),
        (
            "Landshut",
            {
                "key": "bd0c2d0177a0849a905cded5cb734a6f",
                "kommune": 2655,
                "bezirk": 2655,
                "strasse": 763,
                "abfallarten": [31, 17, 19, 218],
            },
        ),
    ]
)


class Source:
    def __init__(self, key, kommune, bezirk, strasse, abfallarten):
        self._key = key
        self._kommune = kommune
        self._bezirk = bezirk
        self._strasse = strasse
        self._abfallarten = abfallarten  # list of integers

    def fetch(self):
        args = {"f_id_kommune": self._kommune, "f_id_strasse": self._strasse}

        if self._bezirk is not None:
            args["f_id_bezirk"] = self._bezirk

        for i in range(len(self._abfallarten)):
            args[f"f_id_abfalltyp_{i}"] = self._abfallarten[i]

        args["f_abfallarten_index_max"] = (len(self._abfallarten),)
        args["f_abfallarten"] = ",".join(map(lambda x: str(x), self._abfallarten))

        now = datetime.datetime.now()
        date2 = now.replace(year=now.year + 1)
        args["f_zeitraum"] = f"{now.strftime('%Y%m%d')}-{date2.strftime('%Y%m%d')}"

        # get csv file
        r = requests.post(
            f"https://api.abfall.io/?key={self._key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=export_csv",
            data=args,
        )

        # prepare csv reader
        reader = csv.reader(r.text.split("\n"), dialect="unix", delimiter=";")

        fieldnames = []  # contains type of waste, e.g. Restmuell, Biomuell, ...

        entries = []
        for line in reader:
            if reader.line_num == 1:
                # store file names from 1st row
                fieldnames = line
            else:
                # process all cells,
                for idx, cell in enumerate(line):
                    if cell != "":
                        # ignore empty cell
                        date = datetime.datetime.strptime(cell, "%d.%m.%Y").date()
                        entries.append(CollectionAppointment(date, fieldnames[idx]))

        return entries

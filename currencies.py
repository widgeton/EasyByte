import json
from pathlib import Path
from decimal import Decimal
import datetime as dt

from currencyapicom import Client


class Loader:
    def __init__(self, token: str) -> None:
        self._client = Client(token)

        self._dir_path = Path('currencies')
        self._dir_path.mkdir(exist_ok=True)

        self._cur_path = self._dir_path / 'currencies.json'
        self._latest_path = self._dir_path / 'latest.json'

    def get_data(self) -> dict:
        if not self._cur_path.is_file():
            self.load_data()

        with open(self._cur_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_data(self) -> None:
        with open(self._cur_path, 'w', encoding='utf-8') as file:
            json.dump(self._client.currencies(), file, indent=2, ensure_ascii=True)

    def get_latest(self) -> dict:
        if not self._latest_path.is_file():
            self.load_latest()

        with open(self._latest_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_latest(self) -> None:
        with open(self._latest_path, 'w', encoding='utf-8') as file:
            json.dump(self._client.latest(), file, indent=2, ensure_ascii=True)


class Currencies:
    def __init__(self, loader: Loader) -> None:
        self._loader = loader
        self._data = self._loader.get_data()
        self._latest = self._loader.get_latest()

    def calculate(self, amount: int, from_cur: str, to_cur: str) -> Decimal:
        val_from_cur = Decimal(self._get_cur_value(from_cur))
        val_to_cur = Decimal(self._get_cur_value(to_cur))
        res = val_to_cur / val_from_cur * amount
        dec_dig = self._data.get('data').get(to_cur).get('decimal_digits')
        return res.quantize(Decimal(f"1.{'0' * dec_dig}"))

    def _get_cur_value(self, cur: str) -> int | float:
        self._update()
        return self._latest.get('data').get(cur).get('value')

    def _update(self) -> None:
        date = self._latest.get('meta').get('last_updated_at')
        if self._is_outdated(date):
            self._loader.load_data()
            self._data = self._loader.get_data()

            self._loader.load_latest()
            self._latest = self._loader.get_latest()

    def _is_outdated(self, date: str, format_: str = "%Y-%m-%dT%H:%M:%SZ") -> bool:
        expired = dt.datetime.utcnow() - dt.timedelta(days=1)
        return dt.datetime.strptime(date, format_) < expired

    def is_existed(self, cur: str) -> bool:
        return cur in self._data.get('data')

    def get_list_currencies(self) -> list[str]:
        return [f"{cur.get('code')} - {cur.get('name')}" for cur in self._data.get('data').values()]

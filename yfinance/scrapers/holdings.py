from io import StringIO

import pandas as pd

from yfinance.data import YfData
from bs4 import BeautifulSoup



class Holdings:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._top = None

    @property
    def top(self) -> pd.DataFrame:
        if self._top is None:
            self._scrape(self.proxy)
        return self._top


    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/holdings', proxy=proxy)
            holdings = pd.read_html(StringIO(resp.text))
            # soup = BeautifulSoup(resp.text, 'html.parser')
            # soup.find()
        except Exception:
            holdings = []

        if len(holdings) >= 1:
            self._top = holdings[0]

from io import StringIO

import pandas as pd
import numpy as np

from yfinance.data import YfData
from bs4 import BeautifulSoup

Returns = ["Annual Total Return (%) History", "Trailing Returns (%) Vs. Benchmarks"]


def reshape(lst, per_row):
    return [ lst[x:x+per_row] for x in range(0, len(lst), per_row) ] 

class Performance:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._returns = None
        self._annual = None

    @property
    def returns(self) -> pd.DataFrame:
        if self._returns is None:
            self._scrape(self.proxy)
        return self._returns

    @property
    def annual(self) -> pd.DataFrame:
        if self._annual is None:
            self._scrape(self.proxy)
        return self._annual

    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/performance', proxy=proxy)
            performance = [] #pd.read_html(StringIO(resp.text))
            soup = BeautifulSoup(resp.text, 'html.parser')
            divs = soup.find_all("div", {"class":"Mb(25px)"})
            for div in divs:
                chld_list = [chld for chld in div.children]
                if len(chld_list) == 2:
                    title = chld_list[0].get_text()
                    if title in Returns:
                        data = np.array(reshape(chld_list[1].get_text("|").split("|"), 3))
                        performance.append(pd.DataFrame(data=data[1:,1:],index=data[1:,0],columns=data[0,1:]))

        except Exception as e:
            print (e)
            performance = []

        if len(performance) >= 2:
            self._returns = performance[0]
            self._annual = performance[1]

from io import StringIO

import pandas as pd
import numpy as np

from yfinance.data import YfData
from bs4 import BeautifulSoup

Returns = ["Overall Portfolio Composition (%)", "Sector Weightings (%)"]

def reshape(lst, per_row):
    return [ lst[x:x+per_row] for x in range(0, len(lst), per_row) ] 


class Holdings:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._top = None
        self._composition = None
        self._sector = None

    @property
    def top(self) -> pd.DataFrame:
        if self._top is None:
            self._scrape(self.proxy)
        return self._top

    @property
    def sector(self) -> pd.DataFrame:
        if self._sector is None:
            self._scrape_div(self.proxy)
        return self._sector
    
    @property
    def composition(self) -> pd.DataFrame:
        if self._composition is None:
            self._scrape_div(self.proxy)
        return self._composition

    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/holdings', proxy=proxy)
            if "holdings" not in resp.url:
                raise Exception("Page not found") 
            holdings = pd.read_html(StringIO(resp.text))
            # soup = BeautifulSoup(resp.text, 'html.parser')
            # soup.find()
        except Exception:
            holdings = []

        if len(holdings) >= 1:
            self._top = holdings[0]

    def _scrape_div(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/holdings', proxy=proxy)
            if "holdings" not in resp.url:
                raise Exception("Page not found") 
            holdings = [] #pd.read_html(StringIO(resp.text))
            soup = BeautifulSoup(resp.text, 'html.parser')
            divs = soup.find_all("div", {"class":"Mb(25px)"})
            for div in divs:
                chld_list = [chld for chld in div.children]
                if len(chld_list) == 2:
                    title = chld_list[0].get_text()
                    if title in Returns:
                        data = np.array(reshape(chld_list[1].get_text("|").split("|"), 2))
                        holdings.append(pd.DataFrame(data=data[0:,0:],index=data[0:,0],columns=data[0,0:]))

        except Exception as e:
            holdings = []

        if len(holdings) >= 2:
            self._composition = holdings[0]
            self._sector = holdings[1]

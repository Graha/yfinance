import re

import pandas as pd
import numpy as np

from yfinance.data import YfData
from bs4 import BeautifulSoup

from . import utils
logger = utils.get_yf_logger()


class Profile:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._moringstar_box = None

    @property
    def moringstar_box(self) -> pd.DataFrame:
        if self._moringstar_box is None:
            self._scrape(self.proxy)
        return self._moringstar_box

    # TODO optimize
    def moringstar_score(self, file_name):
        # image file name to morning star score
        score = []
        for col in ["Large", "Med", "Small"]:
            for row in ["Value", "Blend", "Growth"]:
                score += [col + row]
        result = re.search(r".*3_0stylelargeeq(\d).gif", file_name)
        if result is not None:
            return score[int(result.group(1))-1]
        else:
            return None

    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/profile', proxy=proxy)
            soup = BeautifulSoup(resp.text, 'html.parser')
            imgs = soup.find_all("img",  {"alt": "Morningstar Style Box"})
            for img in imgs:
                self._moringstar_box = self.moringstar_score(img["src"])
                return

        except Exception as e:
            logger.debug(e)
            self._moringstar_box = None

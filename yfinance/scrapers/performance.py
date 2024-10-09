# from io import StringIO

import re
import pandas as pd
import requests

from yfinance import utils
from yfinance.data import YfData
from yfinance.const import _QUERY1_URL_
from yfinance.exceptions import YFDataException

_QUOTE_SUMMARY_URL_ = f"{_QUERY1_URL_}/v10/finance/quoteSummary/"


def subdict(data: dict, keys: list):
    return dict((k, data[k]) for k in keys)


def moringstar_score(file_name):
    # image file name to morning star score
    score = []
    for col in ["Large", "Med", "Small"]:
        for row in ["Value", "Blend", "Growth"]:
            score += [f"{col}-{row}"]
    result = re.search(r".*3_0stylelargeeq(\d).gif", file_name)
    if result is not None:
        return score[int(result.group(1))-1]
    else:
        return None


class Performance:
    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._returns = None
        self._annual = None
        self._profile = None

    @property
    def returns(self) -> pd.DataFrame:
        if self._returns is None:
            self._fetch_and_parse()
        return self._returns

    @property
    def annual(self) -> pd.DataFrame:
        if self._annual is None:
            self._fetch_and_parse()
        return self._annual

    @property
    def profile(self) -> pd.DataFrame:
        if self._profile is None:
            self._fetch_and_parse()
        return self._profile

    def _fetch(self, proxy):
        modules = ','.join(["fundPerformance", "fundProfile"])
        # ["assetProfile", "defaultKeyStatistics", "fundPerformance", "fundProfile", "summaryDetail", "topHoldings", "price", "pageViews", "financialsTemplate", "quoteUnadjustedPerformanceOverview"])
        params_dict = {"modules": modules,
                       "corsDomain": "finance.yahoo.com", "formatted": "fqalse"}
        result = self._data.get_raw_json(f"{_QUOTE_SUMMARY_URL_}/{self._symbol}",
                                         user_agent_headers=self._data.user_agent_headers, params=params_dict, proxy=proxy)
        return result

    def _fetch_and_parse(self):
        try:
            result = self._fetch(self.proxy)
        except requests.exceptions.HTTPError as e:
            utils.get_yf_logger().error(str(e))

            self._returns = pd.DataFrame()
            self._annual = pd.DataFrame()
            self._profile = pd.DataFrame()
            return

        try:
            data = result["quoteSummary"]["result"][0]
            self._parse_returns_performance(data['fundPerformance'])
            self._parse_annual_performance(data['fundPerformance'])
            self._parse_profile_performance(data['fundProfile'])

        except (KeyError, IndexError):
            raise YFDataException("Failed to parse holders json data.")

    @staticmethod
    def _parse_raw_values(data):
        if isinstance(data, dict) and "raw" in data:
            return data["raw"]
        return data

    def _parse_returns_performance(self, data):
        returns = subdict(data, ['trailingReturnsNav']
                          ).get('trailingReturnsNav', {})
        df = pd.DataFrame(returns, index=[0]).transpose().set_axis(
            ['pct'], axis=1)
        self._returns = df.to_string(
            formatters={'pct': '{:,.2%}'.format})

    def _parse_annual_performance(self, data):
        annual = subdict(data, ['annualTotalReturns']
                         ).get('annualTotalReturns', {}).get('returns', {})
        df = pd.DataFrame(annual).set_index('year')
        self._annual = df.to_string(
            formatters={'annualValue': '{:,.2%}'.format})

    def _parse_profile_performance(self, data):
        profile = subdict(data, ['family', 'categoryName', 'legalType'])
        profile["morningstar_rating"] = moringstar_score(
            data.get("styleBoxUrl", ""))
        df = pd.DataFrame(profile, index=[0]).transpose().set_axis(
            ['value'], axis=1)
        self._profile = df

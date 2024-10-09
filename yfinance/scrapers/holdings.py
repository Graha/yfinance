# from io import StringIO

import pandas as pd
import requests

from yfinance import utils
from yfinance.data import YfData
from yfinance.const import _QUERY1_URL_
from yfinance.exceptions import YFDataException

_QUOTE_SUMMARY_URL_ = f"{_QUERY1_URL_}/v10/finance/quoteSummary/"


def subdict(data: dict, keys: list):
    return dict((k, data[k]) for k in keys)


class Holdings:
    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._top = None
        self._composition = None
        self._sector = None
        self._bondRating = None
        self._equityHoldings = None
        self._bondHoldings = None

    @property
    def top(self) -> pd.DataFrame:
        if self._top is None:
            self._fetch_and_parse()
        return self._top

    @property
    def sector(self) -> pd.DataFrame:
        if self._sector is None:
            self._fetch_and_parse()
        return self._sector

    @property
    def composition(self) -> pd.DataFrame:
        if self._composition is None:
            self._fetch_and_parse()
        return self._composition

    @property
    def bondRating(self) -> pd.DataFrame:
        if self._bondRating is None:
            self._fetch_and_parse()
        return self._bondRating

    @property
    def equityHoldings(self) -> pd.DataFrame:
        if self._equityHoldings is None:
            self._fetch_and_parse()
        return self._equityHoldings

    @property
    def bondHoldings(self) -> pd.DataFrame:
        if self._bondHoldings is None:
            self._fetch_and_parse()
        return self._bondHoldings

    def _fetch(self, proxy):
        modules = ','.join(["topHoldings"])
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

            self._top = pd.DataFrame()
            self._composition = pd.DataFrame()
            self._sector = pd.DataFrame()
            self._bondRating = pd.DataFrame()
            self._equityHoldings = pd.DataFrame()
            self._bondHoldings = pd.DataFrame()
            return

        try:
            data = result["quoteSummary"]["result"][0]['topHoldings']
            self._parse_top_holdings(data)
            self._parse_composition(data)
            self._parse_sector(data)
            self._parse_bondRating(data)
            self._parse_bondHoldings(data)
            self._parse_equityHoldings(data)

        except (KeyError, IndexError):
            raise YFDataException("Failed to parse holders json data.")

    @staticmethod
    def _parse_raw_values(data):
        if isinstance(data, dict) and "raw" in data:
            return data["raw"]
        return data

    def _parse_top_holdings(self, data):
        topHoldings = subdict(data, ['holdings']).get('holdings', [])
        df = pd.DataFrame(topHoldings).set_index('symbol')
        self._top = df.to_string(
            formatters={'holdingPercent': '{:,.2%}'.format})

    def _parse_composition(self, data):
        composition = subdict(data, ['stockPosition', 'bondPosition'])
        df = pd.DataFrame(composition, index=[0]).transpose()
        self._composition = df.set_axis(['pct'], axis=1).to_string(
            formatters={'pct': '{:,.2%}'.format})

    def _parse_sector(self, data):
        sector = subdict(data, ['sectorWeightings']).get(
            'sectorWeightings', [])
        _transformed = {k: v for d in sector for k, v in d.items()}
        df = pd.DataFrame(_transformed, index=[0]).transpose()
        self._sector = df.set_axis(['pct'], axis=1).to_string(
            formatters={'pct': '{:,.2%}'.format})

    def _parse_bondRating(self, data):
        bondRating = subdict(data, ['bondRatings']).get('bondRatings', [])
        _transformed = {k: v for d in bondRating for k, v in d.items()}
        df = pd.DataFrame(_transformed, index=[0]).transpose()
        self._sector = df.set_axis(['pct'], axis=1).to_string(
            formatters={'pct': '{:,.2%}'.format})

    def _parse_equityHoldings(self, data):
        equityHoldings = subdict(
            data, ['equityHoldings']).get('equityHoldings', {})
        df = pd.DataFrame(equityHoldings, index=[0]).transpose()
        self._equityHoldings = df.set_axis(['value'], axis=1).to_string(
            formatters={'value': '{:,.2f}'.format})

    def _parse_bondHoldings(self, data):
        bondHoldings = subdict(
            data, ['bondHoldings']).get('bondHoldings', {})
        df = pd.DataFrame(bondHoldings, index=[0]).transpose()
        self._bondHoldings = df.set_axis(['value'], axis=1).to_string(
            formatters={'value': '{:,.2f}'.format})

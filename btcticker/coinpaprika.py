import logging
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

COINPAPRIKA_MODULE = None
if not COINPAPRIKA_MODULE:
    try:
        from coinpaprika import Client

        COINPAPRIKA_MODULE = "coinpaprika"
    except ImportError:
        pass


class Coinpaprika:
    def __init__(self, whichcoin="btc-bitcoin", hours_ago=2):
        if COINPAPRIKA_MODULE is not None:
            self.api_client = Client()
        self.api_client = None
        self.whichcoin = whichcoin
        self.hours_ago = hours_ago

    def getCurrentPrice(self, currency="USD"):
        if self.api_client is None:
            return None
        try:
            ticker = self.api_client.tickers.for_coin(
                self.whichcoin, quotes=(currency,)
            )
            return float(ticker["quotes"][currency]["price"])
        except Exception as e:
            logger.exception(e)
            return None

    def getExchangeUSDPrice(self, exchange, pair, currency="USD"):
        if self.api_client is None:
            return None
        try:
            markets = self.api_client.exchanges.markets(
                exchange_id=exchange, quotes=tuple([currency])
            )
            for market in markets:
                if market["pair"] == pair:
                    return float(market["quotes"][currency]["price"])
            logger.info("Not USD, could not get price.")
            return None

        except Exception as e:
            logger.exception(e)
            return None

    def getHistoricalOHLC(self, start=None, end=None, limit=10):
        if self.api_client is None:
            return None
        if not start:
            start = datetime.now() - timedelta(hours=self.hours_ago)
        if not end:
            end = datetime.now()

        ohlc = self.api_client.coins.historical_OHLC(
            coin_id=self.whichcoin, start=start, end=end, limit=limit
        )

        df = pd.DataFrame(ohlc)
        df.columns = [
            'time_open',
            'time_close',
            'open',
            'high',
            'low',
            'close',
            'volume',
            'market_cap',
        ]
        df['time'] = pd.to_datetime(df['time_open'], unit='ms')

        return df

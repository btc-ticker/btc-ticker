import logging
from datetime import datetime, timedelta
import pandas as pd
from coinpaprika import Client

class Coinpaprika():
    def __init__(self, whichcoin="btc-bitcoin", hours_ago=2):
        self.api_client = Client()
        self.whichcoin = whichcoin
        self.hours_ago = hours_ago

    def getCurrentPrice(self, currency="USD"):
        try:
            ticker = self.api_client.tickers.for_coin(self.whichcoin, quotes=(currency, ))
            return float(ticker["quotes"][currency]["price"])
        except:
            logging.exception("Could not get current price.")
            return None

    def getExchangeUSDPrice(self, exchange, pair, currency="USD"):
        try:
            markets = self.api_client.exchanges.markets(exchange_id=exchange, quotes=tuple([currency]))
            for market in markets:
                if market["pair"] == pair:
                    return float(market["quotes"][currency]["price"])
            logging.info("Not USD, could not get price.")
            return None
            
        except:
            logging.exception("Could not get exchange price.")
            return None

    def getHistoricalOHLC(self, start=None, end=None, limit=10):
        if not start:
            start = datetime.now() - timedelta(hours=self.hours_ago)
        if not end:
            end = datetime.now()

        ohlc = self.api_client.coins.historical_OHLC(
            coin_id=self.whichcoin,
            start=start,
            end=end,
            limit=limit
        )

        df = pd.DataFrame(ohlc)
        df.columns = ['time_open', 'time_close', 'open', 'high', 'low', 'close', 'volume', 'market_cap']
        df['time'] = pd.to_datetime(df['time_open'], unit='ms')

        return df
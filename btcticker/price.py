import logging
import time

from .coingecko import CoinGecko
from .coinpaprika import Coinpaprika

logger = logging.getLogger(__name__)


class Price:
    def __init__(self, fiat="eur", days_ago=1):
        self.coingecko = CoinGecko(whichcoin="bitcoin", days_ago=days_ago)
        self.coinpaprika = Coinpaprika(whichcoin="btc-bitcoin")
        self.min_refresh_time = 120
        self.fiat = fiat
        self.ohlc = {}
        self.price = {}
        self.timeseriesstack = []

    def refresh(self):
        current_time = time.time()
        if (
            'timestamp' in self.price
            and current_time - self.price['timestamp'] < self.min_refresh_time
        ):
            return
        logger.info("Getting Data")

        self.price = {}
        price_update_successfull = False
        try:
            self.price["usd"] = self.coingecko.getCurrentPrice("usd")
            self.price["sat_usd"] = 1e8 / self.price["usd"]
            self.price["fiat"] = self.coingecko.getCurrentPrice(self.fiat)
            self.price["sat_fiat"] = 1e8 / self.price["fiat"]
            self.price["timestamp"] = current_time
            self.ohlc = self.coingecko.getOHLC(self.fiat)
            self.timeseriesstack = self.coingecko.getHistoryPrice(self.fiat)
            price_update_successfull = True
        except Exception as e:
            logger.warn(str(e))
        if not price_update_successfull:
            try:
                self.price["usd"] = self.coinpaprika.getCurrentPrice("USD")
                self.price["sat_usd"] = 1e8 / self.price["usd"]
                self.price["fiat"] = self.coinpaprika.getCurrentPrice(self.fiat.upper())
                self.price["sat_fiat"] = 1e8 / self.price["fiat"]
                self.price["timestamp"] = current_time
                self.timeseriesstack = [self.price["fiat"]]
                self.ohlc = {}
                price_update_successfull = True
            except Exception as e:
                logger.warn(str(e))

    def setDaysAgo(self, days_ago):
        self.coingecko.days_ago = days_ago

    @property
    def days_ago(self):
        return self.coingecko.days_ago

    def getPriceChange(self):
        if len(self.timeseriesstack) < 2:
            return ""

        pricechange = (
            str(
                "%+d"
                % round(
                    (self.timeseriesstack[-1] - self.timeseriesstack[0])
                    / self.timeseriesstack[0]
                    * 100,
                    2,
                )
            )
            + "%"
        )
        return pricechange

    def getPriceNow(self):
        if len(self.timeseriesstack) == 0:
            return ""
        pricenow = self.timeseriesstack[-1]
        if pricenow > 1000:
            pricenowstring = format(int(pricenow), ",")
        else:
            pricenowstring = str(float('%.5g' % pricenow))
        return pricenowstring

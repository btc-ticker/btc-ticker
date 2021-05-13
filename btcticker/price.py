from .coingecko import *


class Price():
    def __init__(self, whichcoin="bitcoin", fiat="eur", days_ago=1):
        self.coingecko = CoinGecko(whichcoin=whichcoin, days_ago=days_ago)
        self.fiat = fiat
        self.ohlc = {}
        self.price = {}
        self.timeseriesstack = []
        
    def refresh(self):

        logging.info("Getting Data")

        self.price = {}
        self.price["usd"] = self.coingecko.getCurrentPrice("usd")
        self.price["gold"] = self.coingecko.getCurrentPrice("xau")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.coingecko.getCurrentPrice(self.fiat)
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        
        self.ohlc1 = self.coingecko.getOHLC(self.fiat, 1)
        self.ohlc2 = self.coingecko.getOHLC(self.fiat, 7)
        self.ohlc3 = self.coingecko.getOHLC(self.fiat, 30)
        self.timeseriesstack = self.coingecko.getHistoryPrice(self.fiat)

    def setDaysAgo(self, days_ago):
        self.coingecko.days_ago = days_ago

    @property
    def days_ago(self):
        return self.coingecko.days_ago

    def getPriceChange(self):
        if len(self.timeseriesstack) == 0:
            return ""
        
        pricechange = str("%+d" % round((self.timeseriesstack[-1]-self.timeseriesstack[0])/self.timeseriesstack[-1]*100,2))+"%"
        return pricechange

    def getPriceNow(self):
        if len(self.timeseriesstack) == 0:
            return ""        
        pricenow = self.timeseriesstack[-1]        
        if pricenow > 1000:
            pricenowstring =format(int(pricenow),",")
        else:
            pricenowstring =str(float('%.5g' % pricenow))
        return pricenowstring
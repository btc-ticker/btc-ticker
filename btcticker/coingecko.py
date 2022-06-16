from pycoingecko import CoinGeckoAPI
import logging
from datetime import datetime, timedelta
import pandas as pd


class CoinGecko():
     def __init__(self, whichcoin="bitcoin", days_ago=1):
          self.cg = CoinGeckoAPI()
          self.whichcoin = whichcoin
          self.days_ago = days_ago

     #def refresh(self):

     def getCurrentPrice(self, currency):
          return float(self.cg.get_coins_markets(currency, ids=self.whichcoin)[0]["current_price"])

     def getExchangeUSDPrice(self, exchange):
          rawlivecoin = self.cg.get_exchanges_tickers_by_id(exchange, coin_ids=self.whichcoin, include_exchange_logo=False)
          liveprice= rawlivecoin['tickers'][0]
          if  liveprice['target']!='USD':
               logging.info("Not USD, could not get price.")
               return None
          return float(liveprice['last'])



     def getHistoryPrice(self, currency):

          logging.info("Getting Data")
          # Get the price

          pricenow = self.getCurrentPrice(currency)
          rawtimeseries = self.cg.get_coin_market_chart_by_id(self.whichcoin, currency, self.days_ago)
          logging.info("Got price for the last "+str(self.days_ago)+" days from CoinGecko")
          timeseriesarray = rawtimeseries['prices']
          timeseriesstack = []
          timeseriesdate = []
          length=len (timeseriesarray)
          i=0
          while i < length:
               timeseriesdate.append(datetime.utcfromtimestamp(timeseriesarray[i][0]/1000))
               timeseriesstack.append(float (timeseriesarray[i][1]))
               i+=1

          timeseriesstack.append(pricenow)
          return timeseriesstack

     def getOHLC(self, currency):
          if self.days_ago <= 1:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 1)
          elif self.days_ago <= 7:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 7)
          elif self.days_ago <= 14:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 14)
          elif self.days_ago <= 30:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 30)
          elif self.days_ago <= 90:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 90)
          elif self.days_ago <= 180:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 180)
          elif self.days_ago <= 365:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, 365)
          else:
               rawohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, "max")

          timeseriesstack = []
          timeseriesdate = []
          length=len (rawohlc)
          i=0
          end_time = datetime.utcfromtimestamp(rawohlc[-1][0]/1000)
          while i < length:
               time = datetime.utcfromtimestamp(rawohlc[i][0]/1000)
               if ((end_time-time).total_seconds() / 60 / 60 / 24 <= self.days_ago):
                    timeseriesdate.append(time)
                    timeseriesstack.append(rawohlc[i][1:])
               i+=1
          return pd.DataFrame(timeseriesstack, index = timeseriesdate, columns=["Open", "High", "Low", "Close"])

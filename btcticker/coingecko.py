from pycoingecko import CoinGeckoAPI
import logging
from datetime import datetime, timedelta

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
          length=len (timeseriesarray)
          i=0
          while i < length:
               timeseriesstack.append(float (timeseriesarray[i][1]))
               i+=1
     
          timeseriesstack.append(pricenow)
          return timeseriesstack                  
          
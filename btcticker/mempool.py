import logging
import requests
import urllib3
import math
import numpy as np


class Mempool():
    def __init__(self, api_url="https://mempool.space/api/", n_fee_blocks=7):
        self.mempoolApiUrl = api_url
        if "mempool.space" in api_url:
            self.url_verify = True
        else:
            urllib3.disable_warnings()
            self.url_verify = False

        self.n_fee_blocks = n_fee_blocks
        self.data = {}
        self.refresh()

    def get_json(self, url):
        return requests.get(url, verify=self.url_verify).json()

    def getMempoolBlocks(self):
        mempoolurl = self.mempoolApiUrl + "v1/fees/mempool-blocks"
        rawmempoolblocks = self.get_json(mempoolurl)
        return rawmempoolblocks

    def getBlocks(self, n=1, start_height=None):
        rawblocks = []
        last_height = None
        for _ in range(n):
            if start_height is None and last_height is None:
                mempoolurl = self.mempoolApiUrl + "blocks"
            elif last_height is None:
                mempoolurl = self.mempoolApiUrl + "blocks/%d" % start_height
            else:
                mempoolurl = self.mempoolApiUrl + "blocks/%d" % (last_height - 1)
            rawblocks += self.get_json(mempoolurl)
            last_height = rawblocks[-1]["height"]
        return rawblocks

    def buildFeeArray(self, rawmempoolblocks):
        minFee = []
        maxFee = []
        medianFee = []
        for n in range(self.n_fee_blocks):
            if len(rawmempoolblocks) > n:
                minFee.append(rawmempoolblocks[n]["feeRange"][0])
                maxFee.append(rawmempoolblocks[n]["feeRange"][-1])
                medianFee.append(np.median(rawmempoolblocks[n]["feeRange"]))
            else:
                minFee.append(rawmempoolblocks[len(rawmempoolblocks)-1]["feeRange"][0])
                maxFee.append(rawmempoolblocks[len(rawmempoolblocks)-1]["feeRange"][-1])
                medianFee.append(np.median(rawmempoolblocks[len(rawmempoolblocks)-1]["feeRange"]))
        return minFee, medianFee, maxFee

    def calcMeanTimeDiff(self, rawblocks):
        lasttime = rawblocks[0]["timestamp"]
        time_diff_sum = 0
        for n in range(len(rawblocks) - 1):
            time_diff_sum += lasttime - rawblocks[n + 1]["timestamp"]
            lasttime = rawblocks[n + 1]["timestamp"]
        return time_diff_sum / (n - 1)

    def getMempool(self):
        mempoolurl = self.mempoolApiUrl + "mempool"
        rawmempool = self.get_json(mempoolurl)
        return rawmempool

    def getBlockHeight(self):
        mempoolurl = self.mempoolApiUrl + "blocks/tip/height"
        lastblocknum = int(self.get_json(mempoolurl))
        return lastblocknum

    def getRecommendedFees(self):
        mempoolurl = self.mempoolApiUrl + "v1/fees/recommended"
        fees = self.get_json(mempoolurl)
        return fees

    def optimizeMedianFee(self, pBlock, nextBlock=None, previousFee=None):
        if previousFee is not None:
            useFee = (pBlock["medianFee"] + previousFee) / 2
        else:
            useFee = pBlock["medianFee"]
        if pBlock["blockVSize"] <= 500000:
            return 1.0
        elif pBlock["blockVSize"] <= 950000 and nextBlock is None:
            multiplier = (pBlock["blockVSize"] - 500000) / 500000
            return max(useFee * multiplier, 1.0)
        return useFee
            
    def refresh(self):
        bestFees = {}
        bestFees["fastestFee"] = -1
        bestFees["halfHourFee"] = -1
        bestFees["hourFee"] = -1
        
        logging.info("Getting Data")
        try:
            rawmempoolblocks = self.getMempoolBlocks()
        except Exception as e:
            logging.exception(e)
   
        rawblocks = self.getBlocks(n=1)
        mean_time_diff = self.calcMeanTimeDiff(rawblocks)
        
        if len(rawmempoolblocks) == 1:
            firstMedianFee = self.optimizeMedianFee(rawmempoolblocks[0])
            secondMedianFee = 1
            thirdMedianFee = 1
        else:
            firstMedianFee = self.optimizeMedianFee(rawmempoolblocks[0], rawmempoolblocks[1])
            if len(rawmempoolblocks) <= 2:
                secondMedianFee = self.optimizeMedianFee(rawmempoolblocks[1], previousFee=firstMedianFee)
            else:
                secondMedianFee = self.optimizeMedianFee(rawmempoolblocks[1], rawmempoolblocks[2], firstMedianFee)
            if len(rawmempoolblocks) <= 2:
                thirdMedianFee = 1.0
            elif len(rawmempoolblocks) <= 3:
                thirdMedianFee = self.optimizeMedianFee(rawmempoolblocks[2], previousFee=secondMedianFee)
            else:
                thirdMedianFee = self.optimizeMedianFee(rawmempoolblocks[2], rawmempoolblocks[3], secondMedianFee)
        
        bestFees["fastestFee"] = firstMedianFee
        bestFees["halfHourFee"] = secondMedianFee
        bestFees["hourFee"] = thirdMedianFee
        
        
        
        vsize = 0
        count = 0
        for block in rawmempoolblocks:
            vsize += block["blockVSize"]
            count += block["nTx"]
            #if vsize / 1024 / 1024 * 3.99 < 300:
            #    th_fee = fee[0]
        
        lastblocknum = self.getBlockHeight()
        minFee, medianFee, maxFee = self.buildFeeArray(rawmempoolblocks)
    
        self.data = {}
        self.data["rawblocks"] = rawblocks
        self.data["count"] = count
        self.data["vsize"] = vsize
        self.data["blocks"] = math.ceil(self.data["vsize"] / 1e6)
        self.data["height"] = lastblocknum
        self.data["minFee"] = minFee
        self.data["maxFee"] = maxFee
        self.data["bestFees"] = bestFees
        self.data["medianFee"] = medianFee
        self.data["meanTimeDiff"] = mean_time_diff

    def getData(self):
        return self.data
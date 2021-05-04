import logging
import requests
import math
import numpy as np


class Mempool():
    def __init__(self, n_fee_blocks=7):
        self.mempoolApiUrl = "https://mempool.space/api/"
        self.n_fee_blocks = n_fee_blocks
        self.data = {}
        self.refresh()

    def getMempoolBlocks(self):
        mempoolurl = self.mempoolApiUrl + "v1/fees/mempool-blocks"
        rawmempoolblocks = requests.get(mempoolurl).json()
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
            rawblocks += requests.get(mempoolurl).json()
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
        rawmempool = requests.get(mempoolurl).json()
        return rawmempool

    def getBlockHeight(self):
        mempoolurl = self.mempoolApiUrl + "blocks/tip/height"
        lastblocknum = int(requests.get(mempoolurl).json())
        return lastblocknum
        
    def refresh(self):
        logging.info("Getting Data")
        rawmempoolblocks = self.getMempoolBlocks()
        rawblocks = self.getBlocks(n=1)
        mean_time_diff = self.calcMeanTimeDiff(rawblocks)
        rawmempool = self.getMempool()
        vsize = 0
        th_fee = 0
        for fee in rawmempool["fee_histogram"]:
            vsize += fee[1]
            if vsize / 1024 / 1024 * 3.99 < 300:
                th_fee = fee[0]
        
        lastblocknum = self.getBlockHeight()
        minFee, medianFee, maxFee = self.buildFeeArray(rawmempoolblocks)
    
        self.data = {}
        self.data["rawblocks"] = rawblocks
        self.data["count"] = rawmempool["count"]
        self.data["vsize"] = rawmempool["vsize"]
        self.data["blocks"] = math.ceil(self.data["vsize"] / 1e6)
        self.data["height"] = lastblocknum
        self.data["minFee"] = minFee
        self.data["maxFee"] = maxFee
        self.data["medianFee"] = medianFee
        self.data["meanTimeDiff"] = mean_time_diff
        self.data["purgingFee"] = th_fee

    def getData(self):
        return self.data
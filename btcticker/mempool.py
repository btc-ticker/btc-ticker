import logging
import requests
import urllib3
import math

from pymempool import MempoolAPI
import numpy as np

BLOCKCHAIN_MODULE = None
if not BLOCKCHAIN_MODULE:
    try:
        from blockchain import statistics
        BLOCKCHAIN_MODULE = "statistics"
    except ImportError:
        pass

class Mempool():
    def __init__(self, api_url="https://mempool.space/api/", n_fee_blocks=7):
        self.fall_back_url = "https://mempool.space/api/"
        self.mempoolApiUrl = api_url
        self.mempool = MempoolAPI(api_base_url=api_url)
        self.n_fee_blocks = n_fee_blocks
        self.timeout = 5
        self.data = {}
        self.refresh()

    def getBlocks(self, n=1, start_height=None):
        rawblocks = []
        last_height = None

        for _ in range(n):
            if start_height is None and last_height is None:
                result = self.mempool.get_blocks()
            elif last_height is None:
                result = self.mempool.get_blocks(start_height)
            else:
                result = self.mempool.get_blocks(last_height - 1)
            if result is not None:
                rawblocks += result
            else:
                return None
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
        self.data = {}
        bestFees = {}
        bestFees["fastestFee"] = -1
        bestFees["halfHourFee"] = -1
        bestFees["hourFee"] = -1

        logging.info("Getting Data")

        lastblocknum = self.mempool.get_block_tip_height()
        if lastblocknum is None and self.mempoolApiUrl != self.fall_back_url:
            self.mempool.api_base_url = self.fall_back_url
            lastblocknum = self.mempool.get_block_tip_height()
            self.mempool.api_base_url = self.mempoolApiUrl
        if lastblocknum is None and BLOCKCHAIN_MODULE is not None:
            stats = statistics.get()
            lastblocknum = stats.total_blocks

        difficulty = self.mempool.get_difficulty_adjustment()
        if difficulty is None and self.mempoolApiUrl != self.fall_back_url:
            self.mempool.api_base_url = self.fall_back_url
            difficulty = self.mempool.get_difficulty_adjustment()
            self.mempool.api_base_url = self.mempoolApiUrl
        if difficulty is None and BLOCKCHAIN_MODULE is not None:
            stats = statistics.get()
            last_retarget = stats.next_retarget - 2016
            minutes_between_blocks = stats.minutes_between_blocks
        else:
            last_retarget = lastblocknum - 2016 + difficulty["remainingBlocks"]
            minutes_between_blocks = difficulty["timeAvg"] / 60000

        rawmempoolblocks = self.mempool.get_mempool_blocks_fee()
        if rawmempoolblocks is None and self.mempoolApiUrl != self.fall_back_url:
            self.mempool.api_base_url = self.fall_back_url
            rawmempoolblocks = self.mempool.get_mempool_blocks_fee()
            self.mempool.api_base_url = self.mempoolApiUrl
        if rawmempoolblocks is not None:
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
            minFee, medianFee, maxFee = self.buildFeeArray(rawmempoolblocks)
            self.data["count"] = count
            self.data["vsize"] = vsize
            self.data["minFee"] = minFee
            self.data["maxFee"] = maxFee
            self.data["bestFees"] = bestFees
            self.data["medianFee"] = medianFee
            self.data["blocks"] = math.ceil(self.data["vsize"] / 1e6)

        rawblocks = self.getBlocks(n=1)
        if rawblocks is None and self.mempoolApiUrl != self.fall_back_url:
            self.mempool.api_base_url = self.fall_back_url
            rawblocks = self.getBlocks(n=1)
            self.mempool.api_base_url = self.mempoolApiUrl
        if rawblocks is not None:
            mean_time_diff = self.calcMeanTimeDiff(rawblocks)
        else:
            mean_time_diff = -1


        self.data["rawblocks"] = rawblocks
        self.data["last_retarget"] = last_retarget
        self.data["minutes_between_blocks"] = minutes_between_blocks

        self.data["height"] = lastblocknum

        self.data["meanTimeDiff"] = mean_time_diff

    def getData(self):
        return self.data
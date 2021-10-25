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
        self.fall_back_url = "https://mempool.space/api/"
        self.n_fee_blocks = n_fee_blocks
        self.timeout = 5
        self.data = {}
        self.refresh()

    def get_json(self, url):
        try:
            return requests.get(url, verify=self.url_verify, timeout=self.timeout).json()
        except requests.exceptions.ReadTimeout as e:
            logging.exception(e)
            return None
        except Exception as e:
            logging.exception(e)
            return None

    def getMempoolBlocks(self, use_fall_back=False):
        if use_fall_back:
            mempoolurl = self.fall_back_url + "v1/fees/mempool-blocks"
        else:
            mempoolurl = self.mempoolApiUrl + "v1/fees/mempool-blocks"
        rawmempoolblocks = self.get_json(mempoolurl)
        return rawmempoolblocks

    def getDifficulty(self, use_fall_back=False):
        if use_fall_back:
            mempoolurl = self.fall_back_url + "v1/difficulty-adjustment"
        else:
            mempoolurl = self.mempoolApiUrl + "v1/difficulty-adjustment"
        difficulty = self.get_json(mempoolurl)
        return difficulty

    def getBlocks(self, n=1, start_height=None, use_fall_back=False):
        rawblocks = []
        last_height = None
        if use_fall_back:
            url = self.fall_back_url
        else:
            url = self.mempoolApiUrl

        for _ in range(n):
            if start_height is None and last_height is None:
                mempoolurl = url + "blocks"
            elif last_height is None:
                mempoolurl = url + "blocks/%d" % start_height
            else:
                mempoolurl = url + "blocks/%d" % (last_height - 1)
            result = self.get_json(mempoolurl)
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

    def getMempool(self, use_fall_back=False):
        if use_fall_back:
            mempoolurl = self.fall_back_url + "mempool"
        else:
            mempoolurl = self.mempoolApiUrl + "mempool"
        rawmempool = self.get_json(mempoolurl)
        return rawmempool


    def getBlockHeight(self, use_fall_back=False):
        if use_fall_back:
            mempoolurl = self.fall_back_url + "blocks/tip/height"
        else:
            mempoolurl = self.mempoolApiUrl + "blocks/tip/height"
        result = self.get_json(mempoolurl)
        if result is None:
            return None
        lastblocknum = int(result)
        return lastblocknum


    def getRecommendedFees(self, use_fall_back=False):
        if use_fall_back:
            mempoolurl = self.fall_back_url + "v1/fees/recommended"
        else:
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
        self.data = {}
        bestFees = {}
        bestFees["fastestFee"] = -1
        bestFees["halfHourFee"] = -1
        bestFees["hourFee"] = -1

        logging.info("Getting Data")
        rawmempoolblocks = self.getMempoolBlocks()
        if rawmempoolblocks is None and self.mempoolApiUrl != self.fall_back_url:
            rawmempoolblocks = self.getMempoolBlocks(use_fall_back=True)
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
            rawblocks = self.getBlocks(n=1, use_fall_back=True)
        if rawblocks is not None:
            mean_time_diff = self.calcMeanTimeDiff(rawblocks)
        else:
            mean_time_diff = -1



        lastblocknum = self.getBlockHeight()
        if lastblocknum is None and self.mempoolApiUrl != self.fall_back_url:
            lastblocknum = self.getBlockHeight(use_fall_back=True)
        if lastblocknum is None:
            lastblocknum = -1



        self.data["rawblocks"] = rawblocks


        self.data["height"] = lastblocknum

        self.data["meanTimeDiff"] = mean_time_diff

    def getData(self):
        return self.data
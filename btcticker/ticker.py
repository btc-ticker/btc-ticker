import math
import time
from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw
import logging
from babel import numbers
from .mempool import *
from blockchain import statistics
from .price import *
from .chart import *
from .config import Config
import os
from datetime import datetime, timedelta


class Ticker():
    def __init__(self, config: Config):
        self.config = config
        self.height = config.main.display_height_pixels
        self.width = config.main.display_width_pixels
        self.fiat = config.main.fiat
        self.orientation = config.main.orientation
        self.inverted = config.main.inverted
        self.mempool = Mempool()
        self.price = Price(fiat=self.fiat, days_ago=1)
        
        self.image = Image.new('L', (self.width, self.height), 255)
        
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
        self.fonthiddenprice = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 30)
        self.font = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 40)
        self.fontHorizontalBlock = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 75)
        self.font_price = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 20)
        self.font_height = ImageFont.truetype(os.path.join(fontdir,'PixelSplitter-Bold.ttf'),18)
        self.font_date = ImageFont.truetype(os.path.join(fontdir,'PixelSplitter-Bold.ttf'),15)
        
        self.fontHorizontalBig = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 100)
        

    def setDaysAgo(self, days_ago):
        self.price.setDaysAgo(days_ago)

    def drawText(self, x, y, text, font):
        self.draw.text((x,y),text,font=font,fill = 0)

    def update(self, mode="fiat", mirror=True):
        self.mempool.refresh()
        self.price.refresh()

        symbolstring=numbers.get_currency_symbol(self.fiat.upper(), locale="en")

        mempool = self.mempool.getData()
        current_price = self.price.price
        pricestack = self.price.timeseriesstack

    
        pricechange = self.price.getPriceChange()
        pricenowstring = self.price.getPriceNow()
        
        stats = statistics.get()
        last_retarget = stats.next_retarget - 2016
        
        last_timestamp = mempool["rawblocks"][0]["timestamp"]
        last_height = mempool["rawblocks"][0]["height"]
        last_retarget_blocks = self.mempool.getBlocks(start_height=last_retarget)
        last_retarget_timestamp = last_retarget_blocks[0]["timestamp"]
        remaining_blocks = 2016 - (last_height - last_retarget_blocks[0]["height"])
        difficulty_epoch_duration = stats.minutes_between_blocks * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
        retarget_mult = 14*24*60*60 / difficulty_epoch_duration
        retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
        retarget_date = datetime.fromtimestamp(retarget_timestamp)
        
    
        self.image = Image.new('L', (self.width, self.height), 255)    # 255: clear the image with white
        self.draw = ImageDraw.Draw(self.image)
        minFee = mempool["minFee"]
        medianFee = mempool["medianFee"]
        maxFee = mempool["maxFee"]
        purgingFee = mempool["purgingFee"]
        # meanTimeDiff = mempool["meanTimeDiff"]
        meanTimeDiff = stats.minutes_between_blocks * 60
        t_min = meanTimeDiff // 60
        t_sec = meanTimeDiff % 60
        blocks = math.ceil(mempool["vsize"] / 1e6)
        count = mempool["count"]
        #draw.text((5,2),'%d - %d - %s' % (mempool["height"], blocks, str(time.strftime("%H:%M"))),font =font_height,fill = 0
        if self.config.main.big_number:
            if mode == "fiat":
                self.drawText(5,2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                price_parts = pricenowstring.split(",")
                
                self.drawText(5, 5, price_parts[0], self.fontHorizontalBig)
                self.drawText(85, 80, price_parts[1], self.fontHorizontalBig)
                self.drawText(5, 100, symbolstring, self.fontHorizontalBlock)
            elif mode == "height" or mode == "newblock":
                self.drawText(5, 2, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                price_parts = pricenowstring.split(",")
                                
                self.drawText(5, 5, str(mempool["height"])[:3], self.fontHorizontalBig)
                self.drawText(85, 80, str(mempool["height"])[3:], self.fontHorizontalBig)

            elif mode == "satfiat":
                self.drawText(5,2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f' % (minFee[0], minFee[1], minFee[2]), self.font_date)
                price_parts = pricenowstring.split(",")
                self.drawText(5, 45, symbolstring+pricenowstring, self.font_price)
                self.drawText(30, 80, '%.0f' % (current_price["sat_fiat"]), self.fontHorizontalBig)               
                self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price)                
                
            elif mode == "usd":
                self.drawText(5,2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                price_parts = format(int(current_price["usd"]), ",").split(",")
                
                self.drawText(5, 5, price_parts[0], self.fontHorizontalBig)
                self.drawText(85, 80, price_parts[1], self.fontHorizontalBig)
                self.drawText(5, 100, "$", self.fontHorizontalBlock)
                
                
            if mode != "newblock" and mode != "height":
                self.drawText(170, 75, str(self.price.days_ago)+"day : "+pricechange, self.font_date)
                self.image.paste(makeSpark(pricestack, figsize=(7,3)) ,(150,20))        
        elif self.config.main.fiat != "usd" and self.config.main.show_usd:
            if mode == "fiat":
                self.drawText(5,2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, '$%.0f' % current_price["usd"], self.font_price)
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                self.drawText(5, 67, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 130, symbolstring, self.font_price)
                self.drawText(20, 100, pricenowstring, self.fontHorizontalBlock)
            elif mode == "height":
                self.drawText(5, 2, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, '$%.0f' % current_price["usd"], self.font_price)
                self.drawText(5, 67, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 100, str(mempool["height"]), self.fontHorizontalBlock)
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)       
            elif mode == "satfiat":
                self.drawText(5, 2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5,25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, '$%.0f' % current_price["usd"], self.font_price)
                self.drawText(5, 67, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                self.drawText(5, 89, symbolstring+pricenowstring, self.font_price)
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price)
                self.drawText(50, 100, '%.0f' % (current_price["sat_fiat"]), self.fontHorizontalBlock)     
                
                
            elif mode == "usd":
                self.drawText(5, 2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, symbolstring+pricenowstring, self.font_price)
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                self.drawText(5, 67, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 130, '$', self.font_price)
                self.drawText(20, 100, format(int(current_price["usd"]), ","), self.fontHorizontalBlock)                
                
            elif mode == "newblock":
                self.drawText(5, 2, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, '%d blks %d txs' % (blocks, count), self.font_price)
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_date,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_price,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
                self.drawText(5, 67, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_price)
                self.drawText(3, 90, str(mempool["height"]), self.fontHorizontalBlock)
                
            if mode != "newblock":
                self.drawText(130, 95, str(self.price.days_ago)+"day : "+pricechange, self.font_date) 
                self.image.paste(makeSpark(pricestack), (100,45))                
        else:
            
            if mode == "fiat":
                self.drawText(5,2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 67, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 130, symbolstring, self.font_price)
                self.drawText(20, 100, pricenowstring, self.fontHorizontalBlock)            
            elif mode == "height":
                self.drawText(5, 2, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 67, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 100, str(mempool["height"]), self.fontHorizontalBlock)
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)       
            elif mode == "satfiat":
                self.drawText(5, 2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5,25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 67, symbolstring+pricenowstring, self.font_price)
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price)
                self.drawText(50, 100, '%.0f' % (current_price["sat_fiat"]), self.fontHorizontalBlock)                 
            elif mode == "usd":
                self.drawText(5, 2, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, symbolstring+pricenowstring, self.font_price)
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                self.drawText(5, 67, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                # self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                self.drawText(5, 130, '$', self.font_price)
                self.drawText(20, 100, format(int(current_price["usd"]), ","), self.fontHorizontalBlock)
               
            elif mode == "newblock":
                self.drawText(5, 2, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                self.drawText(5, 25, 'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                self.drawText(5, 45, '%d blks %d txs' % (blocks, count), self.font_price)
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_date,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_price,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
                self.drawText(5, 67, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_price)
                self.drawText(3, 90, str(mempool["height"]), self.fontHorizontalBlock)
        
            if mode != "newblock":
                self.drawText(130, 95, str(self.price.days_ago)+"day : "+pricechange, self.font_date)
                self.image.paste(makeSpark(pricestack) ,(100,45))
        #draw.text((145,2),str(time.strftime("%H:%M %d %b")),font =font_date,fill = 0)
        if self.orientation == 270 :
            self.image=self.image.rotate(180, expand=True)
        if mirror:
            self.image = ImageOps.mirror(self.image)    
    
    #   If the display is inverted, invert the image usinng ImageOps        
        if self.inverted:
            self.image = ImageOps.invert(self.image)
    #   Send the image to the screen        

    def show(self):
        
        self.image.show()
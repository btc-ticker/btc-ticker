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
import os
from datetime import datetime, timedelta
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
fonthiddenprice = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 30)
font = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 40)
fontHorizontal = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 65)
fontHorizontalBlock = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 75)
font_price = ImageFont.truetype(os.path.join(fontdir,'googlefonts/Roboto-Medium.ttf'), 20)
font_height = ImageFont.truetype(os.path.join(fontdir,'PixelSplitter-Bold.ttf'),18)
font_date = ImageFont.truetype(os.path.join(fontdir,'PixelSplitter-Bold.ttf'),15)


class Ticker():
    def __init__(self, width=264, height=176, fiat="eur", days_ago=1, orientation=90, inverted=False):
        self.height = height
        self.width = width
        self.fiat = fiat
        self.orientation = orientation
        self.inverted = inverted
        self.mempool = Mempool()
        self.price = Price(fiat=fiat, days_ago=days_ago)
        
        self.image = Image.new('L', (width, height), 255)

    def setDaysAgo(self, days_ago):
        self.price.setDaysAgo(days_ago)

    def update(self, mode="fiat", mirror=True):
        self.mempool.refresh()
        self.price.refresh()

        symbolstring=numbers.get_currency_symbol(self.fiat.upper(), locale="en")

        mempool = self.mempool.getData()
        current_price = self.price.price
        pricestack = self.price.timeseriesstack
        
        sparkbitmap = makeSpark(pricestack)
    
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
        draw = ImageDraw.Draw(self.image)
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
        if mode == "fiat":
            
            draw.text((5,2),'%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))),font =font_height,fill = 0)
            draw.text((5,25),'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]),font =font_date,fill = 0)
            draw.text((5,45),'$%.0f' % current_price["usd"],font =font_price,fill = 0)
            #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
            draw.text((5,67),'%.0f sat/$' % (current_price["sat_usd"]),font =font_price,fill = 0)
            draw.text((5,89),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
            draw.text((5,110),symbolstring+pricenowstring,font =fontHorizontal,fill = 0)
        elif mode == "height":
            draw.text((5,2),'%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))),font =font_height,fill = 0)
            draw.text((5,25),'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]),font =font_date,fill = 0)
            draw.text((5,45),'$%.0f' % current_price["usd"],font =font_price,fill = 0)
            #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
            draw.text((5,67),'%.0f sat/$' % (current_price["sat_usd"]),font =font_price,fill = 0)
            draw.text((5,89),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
            draw.text((5,110), str(mempool["height"]), font =fontHorizontal,fill = 0)            
        elif mode == "satfiat":
            draw.text((5,2),'%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))),font =font_height,fill = 0)
            draw.text((5,25),'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]),font =font_date,fill = 0)
            draw.text((5,45),'$%.0f' % current_price["usd"],font =font_price,fill = 0)
            # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
            draw.text((5,67),'%.0f sat/$' % (current_price["sat_usd"]),font =font_price,fill = 0)
            draw.text((5,89),symbolstring+pricenowstring, font =font_price,fill = 0)
            draw.text((5,110), '%.0f' % (current_price["sat_fiat"]), font =fontHorizontal,fill = 0)
        elif mode == "usd":
            draw.text((5,2),'%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))),font =font_height,fill = 0)
            draw.text((5,25),'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]),font =font_date,fill = 0)
            draw.text((5,45), symbolstring+pricenowstring,font =font_price,fill = 0)
            # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
            draw.text((5,67),'%.0f sat/$' % (current_price["sat_usd"]),font =font_price,fill = 0)
            draw.text((5,89),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
            draw.text((5,110),'$%.0f' % current_price["usd"],font =fontHorizontal,fill = 0)            
        elif mode == "newblock":
            draw.text((5,2),'%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))),font =font_height,fill = 0)
            # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_date,fill = 0)
            draw.text((5,25),'fee %.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%0.f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]),font =font_date,fill = 0)
            draw.text((5,45),'%d blks %d txs' % (blocks, count),font =font_price,fill = 0)
            # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_price,fill = 0)
            #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
            draw.text((5,67),'%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")),font =font_price,fill = 0)
            draw.text((3,90), str(mempool["height"]), font =fontHorizontalBlock,fill = 0)            
        
        if mode != "newblock":
            draw.text((130,95),str(self.price.days_ago)+"day : "+pricechange,font =font_date,fill = 0)
            # Print price to 5 significant figures
         #       draw.text((20,120),symbolstring,font =fonthiddenprice,fill = 0)
            self.image.paste(sparkbitmap,(100,45))
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
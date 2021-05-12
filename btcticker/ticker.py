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
    def __init__(self, config: Config, width, height):
        self.config = config
        self.height = width
        self.width = height
        self.fiat = config.main.fiat
        self.orientation = config.main.orientation
        self.inverted = config.main.inverted
        self.mempool = Mempool(api_url=config.main.mempool_api_url)
        self.price = Price(fiat=self.fiat, days_ago=1)
        self.stats = None
        
        self.image = Image.new('L', (self.width, self.height), 255)
        
        self.fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')

        self.font_side = self.buildFont(config.fonts.font_side, config.fonts.font_side_size)        
        self.font_top = self.buildFont(config.fonts.font_top, config.fonts.font_top_size)
        self.font_fee = self.buildFont(config.fonts.font_fee, config.fonts.font_fee_size)
        
        
    def buildFont(self, font_name, font_size):
        google_fontdir = os.path.join(self.fontdir, "googlefonts")
        if os.path.exists(os.path.join(self.fontdir, font_name)):
            return ImageFont.truetype(os.path.join(self.fontdir, font_name), font_size)
        elif os.path.exists(os.path.join(self.fontdir, font_name+".ttf")):
            return ImageFont.truetype(os.path.join(self.fontdir, font_name+ ".ttf"), font_size)
        elif os.path.exists(os.path.join(google_fontdir, font_name)):
            return ImageFont.truetype(os.path.join(google_fontdir, font_name), font_size)
        elif os.path.exists(os.path.join(google_fontdir, font_name+".ttf")):
            return ImageFont.truetype(os.path.join(google_fontdir, font_name+ ".ttf"), font_size)
        else:
            raise Exception("Could not find %s in %s" % (font_name, self.fontdir))

    def setDaysAgo(self, days_ago):
        self.price.setDaysAgo(days_ago)

    def drawText(self, x, y, text, font, anchor="la"):
        w, h = self.draw.textsize(text, font=font)
        #start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
        #w = end_x - start_x
        #h = end_y - start_y        
        self.draw.text((x,y),text,font=font,fill = 0, anchor=anchor)
        return w, h

    def drawTextMax(self, x, y, max_w, max_h, text, font_name, start_font_size=20, anchor="la"):
        font_size = start_font_size - 1
        h = 0
        w = 0
        while h < max_h and w < max_w: 
            font_size += 1
            font = self.buildFont(font_name, font_size)
            start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
            w = end_x - start_x
            h = end_y - start_y
        font_size -= 1
        font = self.buildFont(font_name, font_size)
        #start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
        #w = end_x - start_x
        #h = end_y - start_y
        w, h = self.draw.textsize(text, font=font)
        self.draw.text((x,y), text, font=font,fill = 0, anchor=anchor)
        return w, h, font_size

    def refresh(self):
        self.mempool.refresh()
        self.price.refresh()
        self.stats = statistics.get()
        

    def build(self, mode="fiat", layout="all", mirror=True):

        symbolstring=numbers.get_currency_symbol(self.fiat.upper(), locale="en")

        mempool = self.mempool.getData()
        current_price = self.price.price
        pricestack = self.price.timeseriesstack

        pricechange = self.price.getPriceChange()
        pricenowstring = self.price.getPriceNow()
        
        last_retarget = self.stats.next_retarget - 2016
        
        last_timestamp = mempool["rawblocks"][0]["timestamp"]
        last_height = mempool["rawblocks"][0]["height"]
        last_retarget_blocks = self.mempool.getBlocks(start_height=last_retarget)
        last_retarget_timestamp = last_retarget_blocks[0]["timestamp"]
        remaining_blocks = 2016 - (last_height - last_retarget_blocks[0]["height"])
        difficulty_epoch_duration = self.stats.minutes_between_blocks * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
        retarget_mult = 14*24*60*60 / difficulty_epoch_duration
        retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
        retarget_date = datetime.fromtimestamp(retarget_timestamp)
        
        fee_str = '%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f'
        #fee_str = 'fee %.0f %.0f %.0f %.0f %.0f %.0f %.0f'
        fee_short_str = '%.1f-%.1f-%.1f'
        #fee_short_str = 'fee %.0f %.0f %.0f'
    
        self.image = Image.new('L', (self.width, self.height), 255)    # 255: clear the image with white
        self.draw = ImageDraw.Draw(self.image)
        minFee = mempool["minFee"]
        medianFee = mempool["medianFee"]
        maxFee = mempool["maxFee"]
        # meanTimeDiff = mempool["meanTimeDiff"]
        meanTimeDiff = self.stats.minutes_between_blocks * 60
        t_min = meanTimeDiff // 60
        t_sec = meanTimeDiff % 60
        blocks = math.ceil(mempool["vsize"] / 1e6)
        count = mempool["count"]
        #draw.text((5,2),'%d - %d - %s' % (mempool["height"], blocks, str(time.strftime("%H:%M"))),font =font_top,fill = 0
        if layout == "big":
            if mode == "fiat":
                pos_y = 0
                #w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                #pos_y += h
                image_y = pos_y
                price_parts = pricenowstring.split(",")
                
                w, h, font_size = self.drawTextMax(0, 0, self.width, (self.height-pos_y-10)/2, symbolstring+price_parts[0], self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y - 10, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_fee)
                pos_y += h                
                self.drawText(self.width, self.height, price_parts[1], self.buildFont(self.config.fonts.font_console, font_size), anchor="rs")
                #self.drawText(5, 100, symbolstring, self.buildFont(self.config.fonts.font_console, font_size - 25))
            elif mode == "height" or mode == "newblock":
                pos_y = 0

                image_y = pos_y
                price_parts = pricenowstring.split(",")
                w, h, font_size = self.drawTextMax(0, 0, self.width, (self.height-pos_y-10)/2, str(mempool["height"])[:3], self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y - 10, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_fee)
                pos_y += h                
                self.drawText(self.width, self.height, str(mempool["height"])[3:], self.buildFont(self.config.fonts.font_console, font_size), anchor="rs")

            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_fee)
                pos_y += h
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_console, anchor="rs")              
                
            elif mode == "usd":
                pos_y = 0
                price_parts = format(int(current_price["usd"]), ",").split(",")
                
                w, h, font_size = self.drawTextMax(0, 0, self.width, (self.height-pos_y-10)/2, "$"+price_parts[0], self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y - 10, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_fee)
                pos_y += h                
                self.drawText(self.width - 1, self.height - 1, price_parts[1], self.buildFont(self.config.fonts.font_console, font_size), anchor="rs")
                
        elif layout == "fiat" or (layout == "all" and self.config.main.fiat == "usd"):
            
            if mode == "fiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, symbolstring, self.font_side)
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, pricenowstring.replace(",", ""), self.config.fonts.font_buttom, anchor="rs")
            elif mode == "height":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                pos_y += h
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, str(mempool["height"]), self.config.fonts.font_buttom, anchor="rs")
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)       
            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_side)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)
                w, h = self.drawText(5, 119, "sat", self.font_side)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_side) 
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_buttom, anchor="rs")
            elif mode == "usd":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_side)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_side)
                pos_y += h
                # self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                w, h = self.drawText(5, pos_y, '$', self.font_side)
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, format(int(current_price["usd"]), ""), self.config.fonts.font_buttom, anchor="rs")
               
            elif mode == "newblock":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%d blks %d txs' % (blocks, count), self.font_side)
                pos_y += h
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_fee,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_side,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_side,fill = 0)
                w, h = self.drawText(5, 67, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_side)
                pos_y += h
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, str(mempool["height"]), self.config.fonts.font_buttom, anchor="rs")
        
            if mode != "newblock":
                spark_image = makeSpark(pricestack)
                w, h = spark_image.size
                self.image.paste(spark_image ,(100, image_y))
                if mode != "satfiat":
                    self.drawText(130, image_y + h, str(self.price.days_ago)+"day : "+pricechange, self.font_fee)
        elif layout == "fiatheight":
            if mode == "fiat":
                pos_y = 0
                w, h, font_size = self.drawTextMax(0, pos_y, self.width, (self.height-20) / 2, str(mempool["height"]), self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, '%d blk %.0f %% %d:%d - %s' % (remaining_blocks, (retarget_mult * 100 - 100), t_min, t_sec, str(time.strftime("%H:%M"))), self.font_side)
                pos_y += h
                if self.config.main.fiat == "usd":
                    w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                else:
                    w, h = self.drawText(5, pos_y, '%.0f /%s - $%s - %.0f /$' % (current_price["sat_fiat"], symbolstring, format(int(current_price["usd"]), ""), current_price["sat_usd"]), self.font_side)
                pos_y += h                
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, symbolstring + pricenowstring.replace(",", ""), self.config.fonts.font_buttom, anchor="rs")
            elif mode == "height" or mode == "newblock":
                pos_y = 0
                w, h, font_size = self.drawTextMax(0, pos_y, self.width, (self.height-20) / 2, symbolstring + pricenowstring.replace(",", ""), self.config.fonts.font_buttom, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, '%d blk %.0f %% %d:%d - %s' % (remaining_blocks, (retarget_mult * 100 - 100), t_min, t_sec, str(time.strftime("%H:%M"))), self.font_side)
                pos_y += h
                if self.config.main.fiat == "usd":
                    w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                else:
                    w, h = self.drawText(5, pos_y, '%.0f /%s - $%s - %.0f /$' % (current_price["sat_fiat"], symbolstring, format(int(current_price["usd"]), ""), current_price["sat_usd"]), self.font_side)
                pos_y += h  
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, str(mempool["height"]), self.config.fonts.font_console, anchor="rs")     
            elif mode == "satfiat":
                pos_y = 0
                w, h, font_size = self.drawTextMax(0, pos_y, self.width, (self.height-20) / 2, str(mempool["height"]), self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, '%d blk %.0f %% %d:%d - %s' % (remaining_blocks, (retarget_mult * 100 - 100), t_min, t_sec, str(time.strftime("%H:%M"))), self.font_side)
                pos_y += h
                if self.config.main.fiat == "usd":
                    w, h = self.drawText(5, pos_y, symbolstring + pricenowstring.replace(",", ""), self.font_side)
                else:
                    w, h = self.drawText(5, pos_y, '%s - $%s - %.0f /$' % (symbolstring + pricenowstring.replace(",", ""), format(int(current_price["usd"]), ""), current_price["sat_usd"]), self.font_side)
                pos_y += h  
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, '/%s%.0f' % (symbolstring, current_price["sat_fiat"]), self.config.fonts.font_buttom, anchor="rs")
            elif mode == "usd":
                pos_y = 0
                w, h, font_size = self.drawTextMax(0, pos_y, self.width, (self.height-20) / 2, str(mempool["height"]), self.config.fonts.font_console, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee, anchor="lt")
                pos_y += h
                w, h = self.drawText(5, pos_y, '%d blk %.0f %% %d:%d - %s' % (remaining_blocks, (retarget_mult * 100 - 100), t_min, t_sec, str(time.strftime("%H:%M"))), self.font_side)
                pos_y += h
                if self.config.main.fiat == "usd":
                    w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                else:
                    w, h = self.drawText(5, pos_y, '%.0f /%s - %s - %.0f /$' % (current_price["sat_fiat"], symbolstring, symbolstring + pricenowstring.replace(",", ""), current_price["sat_usd"]), self.font_side)
                pos_y += h  
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, "$"+format(int(current_price["usd"]), ""), self.config.fonts.font_buttom, anchor="rs")
               
        else:
            if mode == "fiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                #self.drawText(5, 25, 'fee %.0f|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_side)
                pos_y += h
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, symbolstring, self.font_side)
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, pricenowstring.replace(",", ""), self.config.fonts.font_buttom, anchor="rs")
            elif mode == "height":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                pos_y += h
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, str(mempool["height"]), self.config.fonts.font_buttom, anchor="rs")
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)       
            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_side)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)
                w, h = self.drawText(5, 119, "sat", self.font_side)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_side)
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_buttom, anchor="rs")
                
                
            elif mode == "usd":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_side)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_side,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_side)
                pos_y += h
                w, h = self.drawText(5, pos_y, '$', self.font_side)          
                self.drawTextMax(self.width - 1, self.height - 1, self.width - w, self.height-pos_y, format(int(current_price["usd"]), ""), self.config.fonts.font_buttom, anchor="rs")
                
            elif mode == "newblock":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_top)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_fee)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%d blks %d txs' % (blocks, count), self.font_side)
                pos_y += h
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_fee,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_side,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_side,fill = 0)
                w, h = self.drawText(5, pos_y, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_side)
                pos_y += h
                self.drawTextMax(self.width - 1, self.height - 1, self.width, self.height-pos_y, str(mempool["height"]), self.config.fonts.font_buttom, anchor="rs")
                
            if mode != "newblock":
                spark_image = makeSpark(pricestack)
                w, h = spark_image.size
                self.image.paste(spark_image ,(100, image_y))                
                if mode != "satfiat":
                    self.drawText(130, image_y + h, str(self.price.days_ago)+"day : "+pricechange, self.font_fee)
  

                
        #draw.text((145,2),str(time.strftime("%H:%M %d %b")),font =font_fee,fill = 0)
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
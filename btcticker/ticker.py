import math
import os
import time
from datetime import datetime

from babel import numbers

from btcticker.chart import makeCandle, makeSpark
from btcticker.config import Config
from btcticker.mempool import Mempool
from btcpriceticker.price import Price

from piltext import ImageDrawer, FontManager, TextGrid


class Ticker:
    def __init__(self, config: Config, width, height):
        self.config = config
        self.height = height
        self.width = width
        self.fiat = config.main.fiat
        self.mempool = Mempool(api_url=config.main.mempool_api_url)
        self.price = Price(fiat=self.fiat, days_ago=1, enable_ohlc=True)
        self.mempool.request_timeout = 20

        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
        self.font_manager = FontManager(fontdir, default_font_size=20, default_font_name="Roboto-Medium")
        self.image = ImageDrawer(width, height, self.font_manager)

        # config.main.orientation, config.main.inverted


    def set_days_ago(self, days_ago):
        self.price.set_days_ago(days_ago)

    def change_size(self, width, height):
        self.height = height
        self.width = width
        self.image.change_size(width, height)

    def set_min_refresh_time(self, min_refresh_time):
        self.price.min_refresh_time = min_refresh_time
        self.mempool.min_refresh_time = min_refresh_time

    def refresh(self):
        self.mempool.refresh()
        self.price.refresh()

    def get_w_factor(self, w, factor=264):
        if w < 0:
            w = 0
        if w > factor:
            w = factor
        return int(w / factor * self.width)

    def get_h_factor(self, h, factor=176):
        if h < 0:
            h = 0
        if h > factor:
            h = factor
        return int(h / factor * self.height)

    def get_next_difficulty_string(
        self,
        remaining_blocks,
        retarget_mult,
        meanTimeDiff,
        time,
        retarget_date=None,
        show_clock=True,
        last_block_time=None,
        last_block_sec_ago=None,
    ):
        t_min = meanTimeDiff // 60
        t_sec = meanTimeDiff % 60

        if show_clock:
            return '%d blk %.1f %% | %s -%d min' % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                self.get_last_block_time(date_and_time=False),
                int(last_block_sec_ago / 60),
            )
        elif retarget_date is not None:
            return '%d blk %.2f%% %s' % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                retarget_date.strftime("%d.%b %H:%M"),
            )
        else:
            return '%d blk %.0f %% %d:%d' % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                t_min,
                t_sec,
            )

    def get_fees_string(self, mempool):
        fee_str = '%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f'
        best_fee_str = "low: %.1f med: %.1f high: %.1f"
        minFee = mempool["minFee"]
        bestFees = mempool["bestFees"]
        if self.config.main.show_best_fees:
            return best_fee_str % (
                bestFees["hourFee"],
                bestFees["halfHourFee"],
                bestFees["fastestFee"],
            )
        else:
            return fee_str % (
                minFee[0],
                minFee[1],
                minFee[2],
                minFee[3],
                minFee[4],
                minFee[5],
                minFee[6],
            )

    def get_fee_string(self, mempool):
        fee_str = '%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f'
        best_fee_str = "Fees: L %.1f M %.1f H %.1f"
        minFee = mempool["minFee"]
        bestFees = mempool["bestFees"]
        if self.config.main.show_best_fees:
            return best_fee_str % (
                bestFees["hourFee"],
                bestFees["halfHourFee"],
                bestFees["fastestFee"],
            )
        return fee_str % (
            minFee[0],
            minFee[1],
            minFee[2],
            minFee[3],
            minFee[4],
            minFee[5],
            minFee[6],
        )

    def get_fee_short_string(self, symbol, mempool, last_block_sec_ago):
        bestFees = mempool["bestFees"]
        hourFee = bestFees["hourFee"]
        halfHourFee = bestFees["halfHourFee"]
        fastestFee = bestFees["fastestFee"]

        if len(symbol) > 0 and bestFees["halfHourFee"] > 10:
            best_fee_str = "%s - lb -%d:%d - l %.0f m %.0f h %.0f"
            return best_fee_str % (
                symbol,
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
                hourFee,
                halfHourFee,
                fastestFee,
            )

        elif len(symbol) > 0 and bestFees["halfHourFee"] < 10:
            best_fee_str = "%s - lb -%d:%d - l %.1f m %.1f h %.1f"
            return best_fee_str % (
                symbol,
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
                hourFee,
                halfHourFee,
                fastestFee,
            )
        elif bestFees["halfHourFee"] < 10:
            best_fee_str = "lb -%d:%d - l %.1f m  %.1f h %.1f"
            return best_fee_str % (
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
                hourFee,
                halfHourFee,
                fastestFee,
            )
        else:
            best_fee_str = "lb -%d:%d - l %.0f m  %.0f h %.0f"
            return best_fee_str % (
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
                hourFee,
                halfHourFee,
                fastestFee,
            )

    def build_message(self, message, mirror=True):
        if not isinstance(message, str):
            return
        self.image.initialize()
        y = 0
        message_per_line = message.split("\n")
        for i in range(len(message_per_line)):
            w, h, font_size = self.image.draw_text(
                message_per_line[i],
                (0, y),
                end=(self.width - 1, self.height - 1),
                font_name=self.config.fonts.font_buttom,
                anchor="lt",
            )
            y += h
        self.image.finalize(mirror=mirror)

    #   Send the image to the screen
    def initialize(self):
        self.image.initialize()

    def build(self, mode="fiat", layout="all", mirror=True):

        mempool = self.mempool.getData()

        if mempool["height"] < 0:
            return
        self.initialize()
        if layout == "big_two_rows":
            self.draw_big_two_rows(mode)
        elif layout == "big_one_row":
            self.draw_big_one_row(mode)
        elif layout == "one_number":
            self.draw_one_number(mode)
        elif layout == "fiat" or (layout == "all" and self.config.main.fiat == "usd"):
            self.draw_fiat(mode)
        elif layout == "fiatheight":
            self.draw_fiat_height(mode)
        elif layout == "ohlc":
            self.draw_ohlc(mode)
        elif layout == "mempool":
            self.draw_mempool(mode)
        else:
            self.draw_all(mode)

        self.image.finalize(mirror=mirror, orientation=self.config.main.orientation, inverted=self.config.main.inverted)

    #   Send the image to the screen

    def show(self):

        self.image.show()

    def get_current_price(self, symbol, with_symbol=False, shorten=True):
        price_str = ""
        current_price = self.price.price
        symbolstring = numbers.get_currency_symbol(self.fiat.upper(), locale="en")
        if symbol == "fiat":
            pricenowstring = self.price.get_price_now()
            price_str = pricenowstring.replace(",", "")
            if with_symbol:
                price_str = symbolstring + price_str
        elif symbol == "usd":
            if with_symbol:
                price_str = "$" + format(int(current_price["usd"]), "")
            else:
                price_str = format(int(current_price["usd"]), "")
        elif symbol == "moscow_time_usd":
            price_str = '%.0f' % (current_price["sat_usd"])
        elif symbol == "sat_per_fiat":
            if with_symbol and shorten:
                price_str = '/{}{:.0f}'.format(symbolstring, current_price["sat_fiat"])
            elif with_symbol and not shorten:
                price_str = '{:.0f} sat/{}'.format(
                    current_price["sat_fiat"], symbolstring
                )
            else:
                price_str = '%.0f' % (current_price["sat_fiat"])
        elif symbol == "sat_per_usd":
            if shorten:
                price_str = "%.0f /$" % (current_price["sat_usd"])
            else:
                price_str = '%.0f sat/$' % (current_price["sat_usd"])

        return price_str

    def get_price_change(self, with_symbol=True):
        pricechange = self.price.get_price_change()
        symbolstring = numbers.get_currency_symbol(self.fiat.upper(), locale="en")
        if with_symbol:
            return " "
        return "   " + str(self.price.days_ago) + "d : " + pricechange

        return symbolstring + "  " + str(self.price.days_ago) + "d : " + pricechange
        return "$" + "  " + str(self.price.days_ago) + "d : " + pricechange

    def get_symbol(self):
        symbolstring = numbers.get_currency_symbol(self.fiat.upper(), locale="en")
        return symbolstring

    def get_current_block_height(self):
        mempool = self.mempool.getData()
        return str(mempool["height"])

    def get_sat_per_fiat(self):
        current_price = self.price.price
        return current_price["sat_fiat"]

    def get_remaining_blocks(self):
        mempool = self.mempool.getData()
        last_height = mempool["last_block"]["height"]
        remaining_blocks = 2016 - (last_height - mempool["retarget_block"]["height"])
        return remaining_blocks

    def get_minutes_between_blocks(self):
        mempool = self.mempool.getData()
        meanTimeDiff = mempool["minutes_between_blocks"] * 60
        t_min = meanTimeDiff // 60
        t_sec = meanTimeDiff % 60
        return f"{t_min}:{t_sec}"

    def get_last_block_time(self, date_and_time=True):
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        if date_and_time:
            return str(last_block_time.strftime("%d.%b %H:%M"))
        else:
            return str(last_block_time.strftime("%H:%M"))

    def get_last_block_time2(self):
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        return f'{int(last_block_sec_ago / 60)}:{last_block_sec_ago % 60} min'

    def get_current_time(self):
        return str(time.strftime("%H:%M"))

    def get_last_block_time3(self):
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        return '%s (%d:%d min ago)' % (
            self.get_last_block_time(),
            int(last_block_sec_ago / 60),
            last_block_sec_ago % 60,
        )

    def draw_4_lines(self, line_str):
        xy = (self.get_w_factor(5),  self.get_h_factor(3))
        xy_end = (self.width, (self.height - self.get_h_factor(15)) / 3)
        w, h, font_size = self.image.draw_text(line_str[0], xy, end=xy_end, font_name=self.config.fonts.font_console, anchor="lt")

        xy = (xy[0], xy[1] + int(h * 0.85))
        xy_end = (self.width, (self.height) / 5 + xy[1])
        w, h, font_size = self.image.draw_text(line_str[1], xy, end=xy_end, font_name=self.config.fonts.font_side, anchor="lt")

        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(line_str[2], xy, font_size=font_size, font_name=self.config.fonts.font_side, anchor="lt")
        start = (self.width - 1, self.height - 1)
        xy_end = (xy[0], xy[1])
        w, h, font_size = self.image.draw_text(line_str[3], start, end=xy_end, font_name=self.config.fonts.font_big, anchor="rs")

    def draw_5_lines(self, line_str):
        xy = (self.get_w_factor(5), self.get_h_factor(3))
        xy_end = (self.width,  (self.height) / 4)
        w, h, font_size = self.image.draw_text(
            line_str[0], xy,
            end=xy_end,
            font_name=self.config.fonts.font_console,
            anchor="lt",
        )
        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[1], xy,
            end=(self.width - 2 * self.get_w_factor(5) + xy[0], (self.height) / 8 - self.get_h_factor(3) + xy[1]),
            font_name=self.config.fonts.font_fee,
            anchor="lt",
        )

        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[2], xy, fontsize=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )
        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[3],xy, fontsize=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )
        
        xy = (xy[0], xy[1] + h)
        xy_end = (xy[0], xy[1])
        w, h, font_size = self.image.draw_text(
            line_str[4],
            (self.width - 1, self.height - 1),
            end=xy_end,
            font_name=self.config.fonts.font_buttom,
            anchor="rs",
        )

    def draw_7_lines_with_image(self, line_str, mode):
        pricestack = self.price.timeseries_stack
        pricechange = self.price.get_price_change()
        xy = ( self.get_w_factor(5), self.get_h_factor(3))
        height_div = 9
        xy_end = (self.width - self.get_w_factor(10) + xy[0],
            (self.height) / height_div + self.get_h_factor(3) + xy[1])
        w, h, font_size = self.image.draw_text(
            line_str[0],
            xy,
            end=xy_end,
            font_name=self.config.fonts.font_top,
            anchor="lt",
        )
        xy = (xy[0], xy[1] + h)
        xy_end=(self.width - self.get_w_factor(10) + xy[0],
            (self.height) / height_div + xy[1])
        w, h, font_size = self.image.draw_text(
            line_str[1],
            xy,
            end=xy_end,
            font_name=self.config.fonts.font_fee,
            anchor="lt",
        )
        xy = (xy[0], xy[1] + h)
        image_y = xy[1]
        xy_end = (self.width / 2 - self.get_w_factor(10) + xy[0],
            (self.height) / height_div - self.get_h_factor(3) + xy[1])
            
        w, h, font_size = self.image.draw_text(
            line_str[2], xy,
            end=xy_end,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )

        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[3], xy,
            font_size=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )

        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[4], xy,
            font_size=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )

        image_text_y = xy[1] + h - self.get_h_factor(1)
        xy = (xy[0], xy[1] + h)
        font_size_image = font_size
        w, h, font_size = self.image.draw_text(
            line_str[5],
            xy,
            font_size=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )
        
        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[6],
            xy,
            font_size=font_size,
            font_name=self.config.fonts.font_side,
            anchor="lt",
        )
        xy_end = (xy[0], self.height - xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[7],
            (self.width - 1, self.height - 1),
            end=xy_end,
            font_name=self.config.fonts.font_buttom,
            anchor="rs",
        )

        spark_image = makeSpark(
            pricestack, figsize_pixel=(self.get_w_factor(170), self.get_h_factor(51))
        )
        w, h = spark_image.size
        self.image.paste(spark_image, (self.get_w_factor(100), image_y))
        if mode != "satfiat":
            xy_end = (self.width, image_text_y - self.get_h_factor(20))
            self.image.draw_text(
                str(self.price.days_ago) + "day : " + pricechange,
                (self.get_w_factor(130), image_text_y),
                end=xy_end,
                font_name=self.config.fonts.font_fee,
                anchor="lt",
            )

    def draw_ohlc(self, mode):
        line_str = ['', '', '', '', '', '', '']
        current_price = self.price.price
        pricechange = self.price.get_price_change()
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_height = mempool["last_block"]["height"]
        meanTimeDiff = mempool["minutes_between_blocks"] * 60
        if mempool["retarget_block"] is not None:
            last_retarget_timestamp = mempool["retarget_block"]["timestamp"]
            remaining_blocks = 2016 - (
                last_height - mempool["retarget_block"]["height"]
            )
            difficulty_epoch_duration = mempool[
                "minutes_between_blocks"
            ] * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
            retarget_mult = 14 * 24 * 60 * 60 / difficulty_epoch_duration
            retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
            retarget_date = datetime.fromtimestamp(retarget_timestamp)
        if mode == "fiat":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                "$"
                + format(int(current_price["usd"]), "")
                + ' - %.0f /%s - %.0f /$'
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = (
                self.get_symbol()
                + "  "
                + str(self.price.days_ago)
                + "d : "
                + pricechange
            )
            line_str[6] = self.get_current_price("fiat")
        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_price("fiat", with_symbol=True)
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                "$"
                + format(int(current_price["usd"]), "")
                + ' - %.0f /%s - %.0f /$'
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = "   " + str(self.price.days_ago) + "d : " + pricechange
            line_str[6] = self.get_current_block_height()
        elif mode == "satfiat":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + " - $"
                + format(int(current_price["usd"]), "")
                + ' - %.0f /$' % (current_price["sat_usd"])
            )
            line_str[5] = (
                "/%s" % self.get_symbol()
                + "  "
                + str(self.price.days_ago)
                + "d : "
                + pricechange
            )
            line_str[6] = self.get_current_price("sat_per_fiat")
        elif mode == "moscowtime":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + " - $"
                + format(int(current_price["usd"]), "")
                + f' - {self.get_sat_per_fiat():.0f} /{self.get_symbol()}'
            )
            line_str[5] = "/$" + "  " + str(self.price.days_ago) + "d : " + pricechange
            line_str[6] = "%.0f" % current_price["sat_usd"]
        elif mode == "usd":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + ' - %.0f /%s - %.0f /$'
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = "$" + "  " + str(self.price.days_ago) + "d : " + pricechange
            line_str[6] = format(int(current_price["usd"]), "")

        line_str[2] = self.get_fee_string(mempool)
        line_str[3] = self.get_next_difficulty_string(
            self.get_remaining_blocks(),
            retarget_mult,
            meanTimeDiff,
            time,
            retarget_date=retarget_date,
            show_clock=False,
        )
        w = 6
        dpi = int(480 / w)

        pos_y = self.get_h_factor(3)

        if self.width > 450 and self.height > self.width:
            xy_end = (self.width, (self.height - self.get_h_factor(20, factor=800)) / 2 + pos_y)
            w, h, font_size = self.image.draw_text(
                line_str[0],
                (0, pos_y),
                end=xy_end,
                font_name=self.config.fonts.font_console,
                anchor="lt",
            )

            pos_y += h - self.get_h_factor(10, factor=800)
            xy_end = (self.width, (self.height - self.get_h_factor(20, factor=800)) / 2 + pos_y)
            w, h, font_size = self.image.draw_text(
                line_str[1],
                (self.get_w_factor(5), pos_y),
                end=xy_end,
                font_name=self.config.fonts.font_side,
                anchor="lt",
            )

            pos_y += h
        else:
            xy_end = (self.width, (self.height - self.get_h_factor(20, factor=800)) / 2 + pos_y)
            w, h, font_size = self.image.draw_text(
                line_str[0],
                (0, pos_y),
                end=xy_end,
                font_name=self.config.fonts.font_console,
                anchor="lt",
            )

            pos_y += h - self.get_h_factor(10, factor=800)
        if self.width > 450 and self.height > self.width:
            ohlc_image = makeCandle(
                self.price.ohlc,
                figsize_pixel=(self.width, self.height * 0.45),
                dpi=dpi,
                x_axis=False,
            )
        else:
            ohlc_image = makeCandle(
                self.price.ohlc,
                figsize_pixel=(self.width, self.height - pos_y),
                dpi=dpi,
                x_axis=False,
            )
        ohlc_w, ohlc_h = ohlc_image.size
        self.image.paste(ohlc_image,(0, pos_y))
        pos_y += ohlc_h
        if self.width > 450 and self.height > self.width:
            xy_end = (0, pos_y)
            w_low, h_low, fs_low = self.image.draw_text(
                line_str[6],
                (self.width - 1, self.height - 1),
                end=xy_end,
                font_name=self.config.fonts.font_buttom,
                anchor="rs",
            )

            xy_end = (self.width / 3, self.height + pos_y)
            w, h_symbolstring, font_size = self.image.draw_text(
                line_str[5],
                (self.get_w_factor(5), self.height - h_low + self.get_h_factor(10, factor=800)),
                end=xy_end,
                font_name=self.config.fonts.font_side,
                anchor="lt",
            )
            xy_end = (self.width, self.height + pos_y)
            w, h, font_size = self.image.draw_text(
                line_str[2],
                (self.get_w_factor(5), pos_y),
                end=xy_end, 
                font_name=self.config.fonts.font_fee,
                anchor="lt",
            )

            pos_y += h
            xy_end = (self.width - self.get_w_factor(50), (self.height - self.get_h_factor(20, factor=800)) / 2 + pos_y)
            w, h, font_size = self.image.draw_text(
                line_str[3],
                (self.get_w_factor(5), pos_y),
                end=xy_end,
                font_name=self.config.fonts.font_side,
                anchor="lt",
            )

            pos_y += h
            xy = (self.get_w_factor(5), self.height
                - h_low
                - h_symbolstring
                - self.get_h_factor(20, factor=800))
                               
            xy_end = (self.width - self.get_w_factor(5), (self.height - self.get_h_factor(20, factor=800)) / 2 + xy[1])
            w, h, font_size = self.image.draw_text(
                line_str[4],
                xy,
                end=xy_end,
                font_name=self.config.fonts.font_side,
            )

            pos_y += h

    def draw_all(self, mode):
        line_str = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        mempool = self.mempool.getData()
        current_price = self.price.price
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        last_height = mempool["last_block"]["height"]
        if mempool["retarget_block"] is not None:
            last_retarget_timestamp = mempool["retarget_block"]["timestamp"]
            remaining_blocks = 2016 - (
                last_height - mempool["retarget_block"]["height"]
            )
            difficulty_epoch_duration = mempool[
                "minutes_between_blocks"
            ] * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
            retarget_mult = 14 * 24 * 60 * 60 / difficulty_epoch_duration
            retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
            retarget_date = datetime.fromtimestamp(retarget_timestamp)
        blocks = math.ceil(mempool["vsize"] / 1e6)
        count = mempool["count"]
        if mode == "newblock":
            xy = (5, 3)
            w, h, font_size = self.image.draw_text(
                '%s - %s - %s'
                % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
                xy,
                font_name=self.config.fonts.font_side,
                font_size=self.config.fonts.font_side_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1]+h)
            fees_string = self.get_fees_string(mempool)
            w, h, font_size = self.image.draw_text(
                fees_string,
                xy,
                font_name=self.config.fonts.font_fee,
                font_size=self.config.fonts.font_fee_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h)
            w, h, fontsize = self.image.draw_text(
                '%d blks %d txs' % (blocks, count),
                xy,
                font_name=self.config.fonts.font_side,
                font_size=self.config.fonts.font_side_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h)
            w, h, font_size = self.image.draw_text(
                '%d blk %.1f%% %s'
                % (
                    self.get_remaining_blocks(),
                    (retarget_mult * 100 - 100),
                    retarget_date.strftime("%d.%b%H:%M"),
                ),
                xy,
                font_name=self.config.fonts.font_side,
                font_size=self.config.fonts.font_side_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h)
            xy_end = (xy[0], self.height - xy[1])
            w, h, font_size = self.image.draw_text(
                self.get_current_block_height(),
                (self.width - 1, self.height - 1),
                end=xy_end,
                fond_name=self.config.fonts.font_buttom,
                anchor="rs",
            )

        else:

            if mode == "fiat":
                if self.config.main.show_block_time:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                else:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )

                line_str[2] = '$%.0f' % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = self.get_symbol() + " "

                line_str[7] = self.get_current_price("fiat")
            elif mode == "height":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = '$%.0f' % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                # line_str[5] = ""
                line_str[7] = self.get_current_block_height()
            elif mode == "satfiat":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = '$%.0f' % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/%s " % self.get_symbol()
                line_str[7] = self.get_current_price("sat_per_fiat")
            elif mode == "moscowtime":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = self.get_current_price("usd", with_symbol=True)
                line_str[3] = self.get_current_price(
                    "sat_per_fiat", with_symbol=True, shorten=False
                )
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/$ "
                line_str[7] = self.get_current_price("moscow_time_usd")
            elif mode == "usd":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = self.get_current_price("fiat", with_symbol=True)
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = '$ '
                line_str[6] = ' '
                line_str[7] = format(int(current_price["usd"]), "")

            line_str[1] = self.get_fees_string(mempool)

            self.draw_7_lines_with_image(line_str, mode)

    def draw_fiat(self, mode):
        line_str = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        last_height = mempool["last_block"]["height"]
        if mempool["retarget_block"] is not None:
            last_retarget_timestamp = mempool["retarget_block"]["timestamp"]
            remaining_blocks = 2016 - (
                last_height - mempool["retarget_block"]["height"]
            )
            difficulty_epoch_duration = mempool[
                "minutes_between_blocks"
            ] * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
            retarget_mult = 14 * 24 * 60 * 60 / difficulty_epoch_duration
            retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
            retarget_date = datetime.fromtimestamp(retarget_timestamp)
        meanTimeDiff = mempool["minutes_between_blocks"] * 60
        blocks = math.ceil(mempool["vsize"] / 1e6)
        count = mempool["count"]
        current_price = self.price.price
        if mode == "newblock":
            xy = (5, 0)
            w, h, font_size = self.image.draw_text(
                '%s - %s - %s'
                % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
                xy,
                font_name=self.config.fonts.font_top,
                font_size=self.config.fonts.font_top_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h)
            fees_string = self.get_fees_string(mempool)
            w, h, font_size = self.image.draw_text(
                fees_string,
                xy,
                font_name=self.config.fonts.font_fee,
                font_size=self.config.fonts.font_fee_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h)
            w, h, font_size = self.image.draw_text(
                '%d blks %d txs' % (blocks, count),
                xy,
                font_name=self.config.fonts.font_side,
                font_size=self.config.fonts.font_side_size,
                anchor="lt",
            )
            xy = (xy[0], xy[1] + h) 
            diff_string = self.get_next_difficulty_string(
                self.get_remaining_blocks(),
                retarget_mult,
                meanTimeDiff,
                time,
                retarget_date=retarget_date,
                show_clock=False,
            )
            w, h, font_size = self.image.draw_text(
                diff_string,
                (5,67),
                font_name=self.config.fonts.font_side,
                font_size=self.config.fonts.font_side_size,
                anchor="lt",
            )
            xy_end = (self.width, self.height-xy[1] - h) 
            xy = (xy[0], self.height)
            w, h, font_size = self.image.draw_text(
                self.get_current_block_height(),
                xy,
                end=xy_end,
                font_name=self.config.fonts.font_buttom,
                anchor="ls",
            )

        else:
            if mode == "fiat":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = 'lb -%d:%d' % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = '%d blk' % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = self.get_symbol()
                line_str[6] = " "
                line_str[7] = self.get_current_price("fiat")
            elif mode == "height":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = 'lb -%d:%d' % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = '%d blk' % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = " "
                line_str[6] = " "
                line_str[7] = self.get_current_block_height()
            elif mode == "satfiat":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = 'lb -%d:%d' % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = '%d blk' % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/%s" % self.get_symbol()
                line_str[7] = self.get_current_price("sat_per_fiat")
            elif mode == "moscowtime":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = 'lb -%d:%d' % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = '%d blk' % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/$"
                line_str[7] = self.get_current_price("moscow_time_usd")
            elif mode == "usd":
                if not self.config.main.show_block_time:
                    line_str[0] = '{} - {} - {}'.format(
                        self.get_current_block_height(),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = '%s-%s-%d min' % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = 'lb -%d:%d' % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = '%d blk' % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = '$'
                line_str[6] = format(int(current_price["usd"]), "")

            line_str[1] = self.get_fees_string(mempool)

            self.draw_7_lines_with_image(line_str, mode)

    def draw_fiat_height(self, mode):
        line_str = ['', '', '', '', '']
        current_price = self.price.price
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_height = mempool["last_block"]["height"]
        remaining_blocks = 2016 - (last_height - mempool["retarget_block"]["height"])
        meanTimeDiff = mempool["minutes_between_blocks"] * 60
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        if mempool["retarget_block"] is not None:
            last_retarget_timestamp = mempool["retarget_block"]["timestamp"]
            remaining_blocks = 2016 - (
                last_height - mempool["retarget_block"]["height"]
            )
            difficulty_epoch_duration = mempool[
                "minutes_between_blocks"
            ] * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
            retarget_mult = 14 * 24 * 60 * 60 / difficulty_epoch_duration
        if mode == "fiat":
            line_str[0] = self.get_current_block_height()
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("sat_per_fiat", with_symbol=True)
            else:
                line_str[3] = '{:.0f} /{} - ${} - {:.0f} /$'.format(
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    format(int(current_price["usd"]), ""),
                    current_price["sat_usd"],
                )
            line_str[4] = self.get_current_price("fiat", with_symbol=True)
        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_price("fiat", with_symbol=True)
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("sat_per_fiat", with_symbol=True)
            else:
                line_str[3] = '{:.0f} /{} - ${} - {:.0f} /$'.format(
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    format(int(current_price["usd"]), ""),
                    current_price["sat_usd"],
                )
            line_str[4] = self.get_current_block_height()
        elif mode == "satfiat":
            line_str[0] = self.get_current_block_height()
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("fiat", with_symbol=True)
            else:
                line_str[3] = '{} - ${} - {:.0f} /$'.format(
                    self.get_current_price("fiat", with_symbol=True),
                    format(int(current_price["usd"]), ""),
                    current_price["sat_usd"],
                )
            line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
        elif mode == "moscowtime":
            line_str[0] = self.get_current_block_height()
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("fiat", with_symbol=True)
            else:
                line_str[3] = '{} - ${} - {:.0f} /$'.format(
                    self.get_current_price("fiat", with_symbol=True),
                    format(int(current_price["usd"]), ""),
                    current_price["sat_usd"],
                )
            line_str[4] = '/$%.0f' % (current_price["sat_usd"])
        elif mode == "usd":
            line_str[0] = self.get_current_block_height()
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("sat_per_fiat", with_symbol=True)
            else:
                line_str[3] = '{:.0f} /{} - {} - {:.0f} /$'.format(
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    self.get_current_price("fiat", with_symbol=True),
                    current_price["sat_usd"],
                )
            line_str[4] = self.get_current_price("usd")

        line_str[1] = self.get_fee_string(mempool)
        line_str[2] = self.get_next_difficulty_string(
            self.get_remaining_blocks(),
            retarget_mult,
            meanTimeDiff,
            time,
            last_block_time=last_block_time,
            last_block_sec_ago=last_block_sec_ago,
        )

        self.draw_5_lines(line_str)

    def draw_mempool(self, mode):
        mempool = self.mempool.getData()

        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        last_height = mempool["last_block"]["height"]
        if mempool["retarget_block"] is not None:
            last_retarget_timestamp = mempool["retarget_block"]["timestamp"]
            remaining_blocks = 2016 - (
                last_height - mempool["retarget_block"]["height"]
            )
            difficulty_epoch_duration = mempool[
                "minutes_between_blocks"
            ] * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
            retarget_mult = 14 * 24 * 60 * 60 / difficulty_epoch_duration
        meanTimeDiff = mempool["minutes_between_blocks"] * 60
        line_str = ['', '', '', '']
        if mode == "fiat":
            line_str[0] = self.get_current_price("fiat")
            line_str[2] = '%s - %.0f /%s - lb -%d:%d' % (
                self.get_current_block_height(),
                self.get_sat_per_fiat(),
                self.get_symbol(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_block_height()
            line_str[2] = '%s - %.0f /%s - lb -%d:%d' % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_sat_per_fiat(),
                self.get_symbol(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "satfiat":
            line_str[0] = self.get_current_price("sat_per_fiat", with_symbol=True)
            line_str[2] = '%s - %s - lb -%d:%d' % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_current_block_height(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "moscowtime":
            line_str[0] = self.get_current_price("sat_per_usd", shorten=True)
            line_str[2] = '%s - %s - lb -%d:%d' % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_current_block_height(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "usd":
            line_str[0] = self.get_current_price("usd")
            line_str[2] = '%s - %s - lb -%d:%d' % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_current_block_height(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )
        line_str[1] = self.get_next_difficulty_string(
            self.get_remaining_blocks(),
            retarget_mult,
            meanTimeDiff,
            time,
            last_block_time=last_block_time,
            last_block_sec_ago=last_block_sec_ago,
        )
        if mempool["bestFees"]["hourFee"] > 10:
            line_str[3] = "%d %d %d" % (
                mempool["bestFees"]["hourFee"],
                mempool["bestFees"]["halfHourFee"],
                mempool["bestFees"]["fastestFee"],
            )
        else:
            line_str[3] = "{:.1f} {:.1f} {:.1f}".format(
                mempool["bestFees"]["hourFee"],
                mempool["bestFees"]["halfHourFee"],
                mempool["bestFees"]["fastestFee"],
            )

        self.draw_4_lines(line_str)

    def draw_big_two_rows(self, mode):
        current_price = self.price.price
        pricenowstring = self.price.get_price_now()
        line_str = ['', '', '']
        if mode == "fiat":
            price_parts = pricenowstring.split(",")

            line_str[0] = self.get_symbol() + price_parts[0]
            line_str[1] = '{} - {} - {}'.format(
                self.get_current_block_height(),
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[2] = price_parts[1]
        elif mode == "height" or mode == "newblock":
            price_parts = pricenowstring.split(",")
            line_str[0] = self.get_current_block_height()[:3]
            line_str[1] = '{} - {} - {}'.format(
                self.get_symbol() + pricenowstring,
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[2] = self.get_current_block_height()[3:]
        elif mode == "satfiat":
            line_str[0] = "sat/%s" % self.get_symbol()
            line_str[1] = '{} - {} - {}'.format(
                self.get_symbol() + pricenowstring,
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[2] = self.get_current_price("sat_per_fiat")
        elif mode == "moscowtime":
            line_str[0] = "sat/$"
            line_str[1] = '{} - {} - {}'.format(
                self.get_symbol() + pricenowstring,
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[2] = self.get_current_price("moscow_time_usd")
        elif mode == "usd":
            price_parts = format(int(current_price["usd"]), ",").split(",")

            line_str[0] = "$" + price_parts[0]
            line_str[1] = '{} - {} - {}'.format(
                self.get_current_block_height(),
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[2] = price_parts[1]

        pos_y = self.get_h_factor(3)
        if line_str[0] != "":
            xy_end = (self.width - self.get_w_factor(5), (self.height - self.get_h_factor(10)))
            w, h, font_size = self.image.draw_text(
                line_str[0] + " ",
                (self.get_w_factor(5), pos_y),
                end=xy_end,
                font_name=self.config.fonts.font_console,
                anchor="lt",
            )

            pos_y += h
        xy_end = (self.width - self.get_w_factor(5), (self.height - pos_y - self.get_h_factor(15)))
        w, h, font_size = self.image.draw_text(
            line_str[1],
            (self.get_w_factor(5), pos_y),
            end=xy_end,
            font_name=self.config.fonts.font_fee,
            anchor="lt",
        )

        pos_y += h
        xy_end= (self.width - 1, (self.height - pos_y - self.get_h_factor(15)))
        w, h, font_size = self.image.draw_text(
            line_str[2],
            (self.width - 1, self.height - 1),
            end=xy_end,
            font_name=self.config.fonts.font_big,
            anchor="rs",
        )

    def draw_one_number(self, mode):
        line_str = ['', '']
        if mode == "fiat":
            line_str[0] = self.get_current_price("fiat", with_symbol=True)
            line_str[1] = 'Market price of bitcoin'
        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_block_height()
            line_str[1] = 'Number of blocks in the blockchain'
        elif mode == "satfiat":
            line_str[0] = self.get_current_price("sat_per_fiat", with_symbol=True)
            line_str[1] = 'Value of one %s in sats' % self.get_symbol()
        elif mode == "moscowtime":
            line_str[1] = 'moscow time'
            line_str[0] = self.get_current_price("moscow_time_usd")
        elif mode == "usd":
            line_str[0] = self.get_current_price("usd")
            line_str[1] = 'Market price of bitcoin'

        pos_y = self.get_w_factor(30)
        xy = (self.get_w_factor(5), self.height - self.get_h_factor(15))
        xy_end = (self.width - self.get_w_factor(10), self.get_h_factor(50))
        w, h, font_size = self.image.draw_text(
            line_str[1],
            xy,
            end=xy_end,
            font_name=self.config.fonts.font_fee,
            anchor="lb",
        )
        xy = (self.width - self.get_w_factor(20), pos_y)
        xy_end = (self.get_w_factor(20), self.height - h - self.get_h_factor(15))
        w, h, font_size = self.image.draw_text(
            line_str[0],
            xy,
            end=xy_end,
            font_name=self.config.fonts.font_fee,
            anchor="rt",
        )

    def draw_big_one_row(self, mode):
        line_str = ['', '', '']
        mempool = self.mempool.getData()
        if mode == "fiat":
            if not self.config.main.show_block_time:
                line_str[0] = '%s - %d - %s - %s' % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                )
            else:
                line_str[0] = '{} - {} - {}'.format(
                    self.get_current_block_height(),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                )
            line_str[1] = self.get_symbol()
            line_str[2] = self.get_current_price("fiat")
        elif mode == "height" or mode == "newblock":
            if not self.config.main.show_block_time:
                line_str[0] = '%s - %d - %s - %s' % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                )
            else:
                line_str[0] = '{} - {} - {}'.format(
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                )

            # line_str[1] = ""
            line_str[2] = self.get_current_block_height()
        elif mode == "satfiat":
            if not self.config.main.show_block_time:
                line_str[0] = '%s - %d - %s - %s' % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                )
            else:
                line_str[0] = '{} - {} - {}'.format(
                    self.get_current_block_height(),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                )
            line_str[1] = "/%s" % self.get_symbol()
            line_str[2] = self.get_current_price("sat_per_fiat")
        elif mode == "moscowtime":
            if not self.config.main.show_block_time:
                line_str[0] = '%s - %d - %s - %s' % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                )
            else:
                line_str[0] = '{} - {} - {}'.format(
                    self.get_current_block_height(),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                )
            line_str[1] = "/$"
            line_str[2] = self.get_current_price("moscow_time_usd")
        elif mode == "usd":
            if not self.config.main.show_block_time:
                line_str[0] = '%s - %d - %s - %s' % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                )
            else:
                line_str[0] = '{} - {} - {}'.format(
                    self.get_current_block_height(),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                )
            line_str[1] = "$"
            line_str[2] = self.get_current_price("usd")

        line_str[1] = self.get_fee_string(mempool)

        xy = (self.get_w_factor(5), self.get_h_factor(3))
        w, h, font_size = self.image.draw_text(
            line_str[0],
            xy,
            end=(self.width,
            (self.height - self.get_h_factor(47))),
            font_name=self.config.fonts.font_fee,
            anchor="lt",
        )

        xy = (xy[0], xy[1] + h)
        # font_size = self.drawer.calculate_font_size(
        #    self.width - self.get_w_factor(5),
        #    self.height - pos_y - self.get_h_factor(15),
        #    line_str[1],
        #    self.config.fonts.font_fee,
        #    anchor="lt",
        # )
        w, h, font_size = self.image.draw_text(
            line_str[1],
            xy, font_size=font_size,
            font_name=self.config.fonts.font_fee,
            anchor="lt",
        )
        
        xy = (xy[0], xy[1] + h)
        w, h, font_size = self.image.draw_text(
            line_str[2],
            (self.width - 1,
            self.height - 1),
            end=(xy[0], xy[1]-self.get_h_factor(15)),
            font_name=self.config.fonts.font_big,
            anchor="rs",
        )

    def get_image(self):
        return self.image.image_handler.image

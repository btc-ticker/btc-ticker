import math
import os
import time
from datetime import datetime

from babel import numbers

from btcticker.chart import makeCandle, makeSpark
from btcticker.config import Config
from btcticker.drawer import Drawer
from btcticker.mempool import Mempool
from btcticker.price import Price


class Ticker:
    def __init__(self, config: Config, width, height):
        self.config = config
        self.height = width
        self.width = height
        self.fiat = config.main.fiat
        self.mempool = Mempool(api_url=config.main.mempool_api_url)
        self.price = Price(fiat=self.fiat, days_ago=1)
        self.mempool.request_timeout = 20

        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')

        self.drawer = Drawer(
            width, height, config.main.orientation, config.main.inverted, fontdir
        )

        self.font_side = self.drawer.buildFont(
            config.fonts.font_side, config.fonts.font_side_size
        )
        self.font_top = self.drawer.buildFont(
            config.fonts.font_top, config.fonts.font_top_size
        )
        self.font_fee = self.drawer.buildFont(
            config.fonts.font_fee, config.fonts.font_fee_size
        )

    def rebuildFonts(self, side_size=None, top_size=None, fee_size=None):
        if side_size is not None:
            self.font_side = self.drawer.buildFont(
                self.config.fonts.font_side, side_size
            )
        if top_size is not None:
            self.font_top = self.drawer.buildFont(self.config.fonts.font_top, top_size)
        if fee_size is not None:
            self.font_fee = self.drawer.buildFont(self.config.fonts.font_fee, fee_size)

    def setDaysAgo(self, days_ago):
        self.price.setDaysAgo(days_ago)

    def _change_size(self, width, height):
        self.height = width
        self.width = height
        self.drawer._change_size(width, height)

    def set_min_refresh_time(self, min_refresh_time):
        self.price.min_refresh_time = min_refresh_time
        self.mempool.min_refresh_time = min_refresh_time

    def refresh(self):
        self.mempool.refresh()
        self.price.refresh()

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
        self.drawer.initialize()
        y = 0
        message_per_line = message.split("\n")
        for i in range(len(message_per_line)):
            font_size = self.drawer.calc_font_size(
                self.width,
                self.height,
                message_per_line[i],
                self.config.fonts.font_buttom,
                anchor="lt",
            )
            w, h = self.drawer.draw_text(
                0,
                y,
                font_size,
                message_per_line[i],
                self.config.fonts.font_buttom,
                anchor="lt",
            )
            y += h
        self.drawer.finalize(mirror=mirror)

    #   Send the image to the screen

    def build(self, mode="fiat", layout="all", mirror=True):

        mempool = self.mempool.getData()

        if mempool["height"] < 0:
            return
        self.drawer.initialize()
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

        self.drawer.finalize(mirror=mirror)

    #   Send the image to the screen

    def show(self):

        self.drawer.show()

    def get_current_price(self, symbol, with_symbol=False, shorten=True):
        price_str = ""
        current_price = self.price.price
        symbolstring = numbers.get_currency_symbol(self.fiat.upper(), locale="en")
        if symbol == "fiat":
            pricenowstring = self.price.getPriceNow()
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
        pricechange = self.price.getPriceChange()
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
        factor5_w = int(5 / 264 * self.width)
        factor3_h = int(3 / 176 * self.height)
        factor15_h = int(15 / 176 * self.height)

        pos_y = factor3_h
        font_size = self.drawer.calc_font_size(
            self.width - factor5_w,
            (self.height - factor15_h) / 3,
            line_str[0],
            self.config.fonts.font_console,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[0],
            self.config.fonts.font_console,
            anchor="lt",
        )
        pos_y += int(h * 0.85)

        font_size = self.drawer.calc_font_size(
            self.width - factor5_w,
            self.height / 5,
            line_str[1],
            self.config.fonts.font_side,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[1],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[2],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h

        font_size = self.drawer.calc_font_size(
            self.width,
            self.height - pos_y,
            line_str[3],
            self.config.fonts.font_big,
            anchor="rs",
        )
        self.drawer.draw_text(
            self.width - 1,
            self.height - 1,
            font_size,
            line_str[3],
            self.config.fonts.font_big,
            anchor="rs",
        )

    def draw_5_lines(self, line_str):
        factor5_w = int(5 / 264 * self.width)
        factor3_h = int(3 / 176 * self.height)

        pos_y = factor3_h
        font_size = self.drawer.calc_font_size(
            self.width - factor5_w,
            (self.height) / 4 - factor3_h,
            line_str[0],
            self.config.fonts.font_console,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[0],
            self.config.fonts.font_console,
            anchor="lt",
        )
        pos_y += h
        font_size = self.drawer.calc_font_size(
            self.width - 2 * factor5_w,
            (self.height) / 8 - factor3_h,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        pos_y += h
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[2],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[3],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h

        font_size = self.drawer.calc_font_size(
            self.width,
            self.height - pos_y,
            line_str[4],
            self.config.fonts.font_buttom,
            anchor="rs",
        )
        self.drawer.draw_text(
            self.width - 1,
            self.height - 1,
            font_size,
            line_str[4],
            self.config.fonts.font_buttom,
            anchor="rs",
        )

    def draw_7_lines_with_image(self, line_str, mode):
        pricestack = self.price.timeseriesstack
        pricechange = self.price.getPriceChange()
        factor5_w = int(5 / 264 * self.width)
        factor10_w = int(10 / 264 * self.width)
        factor100_w = int(100 / 264 * self.width)
        factor130_w = int(130 / 264 * self.width)
        factor170_w = int(170 / 264 * self.width)
        factor3_h = int(3 / 176 * self.height)
        factor51_h = int(51 / 176 * self.height)

        pos_y = factor3_h
        height_div = 10
        font_size = self.drawer.calc_font_size(
            self.width - factor10_w,
            (self.height) / height_div - factor3_h,
            line_str[0],
            self.config.fonts.font_top,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[0],
            self.config.fonts.font_top,
            anchor="lt",
        )
        pos_y += h
        font_size = self.drawer.calc_font_size(
            self.width - factor10_w,
            (self.height) / height_div - factor3_h,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        pos_y += h
        image_y = pos_y
        font_size = self.drawer.calc_font_size(
            self.width / 2 - factor10_w,
            (self.height) / height_div - factor3_h,
            line_str[2],
            self.config.fonts.font_side,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[2],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h

        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[3],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h

        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[4],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h
        image_text_y = pos_y
        font_size_image = font_size

        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[5],
            self.config.fonts.font_side,
            anchor="lt",
        )
        pos_y += h
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[6],
            self.config.fonts.font_side,
            anchor="lt",
        )
        font_size = self.drawer.calc_font_size(
            self.width - w,
            self.height - pos_y,
            line_str[7],
            self.config.fonts.font_buttom,
            anchor="rs",
        )
        self.drawer.draw_text(
            self.width - 1,
            self.height - 1,
            font_size,
            line_str[7],
            self.config.fonts.font_buttom,
            anchor="rs",
        )

        spark_image = makeSpark(pricestack, figsize_pixel=(factor170_w, factor51_h))
        w, h = spark_image.size
        self.drawer.paste(spark_image, (factor100_w, image_y))
        if mode != "satfiat":
            self.drawer.draw_text(
                factor130_w,
                image_text_y,
                font_size_image,
                str(self.price.days_ago) + "day : " + pricechange,
                self.config.fonts.font_fee,
                anchor="lt",
            )

    def draw_ohlc(self, mode):
        line_str = ['', '', '', '', '', '', '']
        current_price = self.price.price
        pricechange = self.price.getPriceChange()
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
        dpi = int(528 / w)

        factor5_w = int(5 / 528 * self.width)
        factor3_h = int(3 / 880 * self.height)
        factor10_h = int(10 / 880 * self.height)
        factor20_h = int(20 / 880 * self.height)
        pos_y = factor3_h

        if self.width > 450 and self.height > self.width:
            font_size = self.drawer.calc_font_size(
                self.width,
                (self.height - factor20_h) / 2,
                line_str[0],
                self.config.fonts.font_console,
                anchor="lt",
            )
            w, h = self.drawer.draw_text(
                0,
                pos_y,
                font_size,
                line_str[0],
                self.config.fonts.font_console,
                anchor="lt",
            )
            pos_y += h - factor10_h
            self.rebuildFonts(side_size=34, fee_size=35)
            w, h = self.drawer.drawText(factor5_w, pos_y, line_str[1], self.font_side)
            pos_y += h
        else:
            font_size = self.drawer.calc_font_size(
                self.width,
                (self.height - factor20_h) / 2,
                line_str[0],
                self.config.fonts.font_console,
                anchor="lt",
            )
            w, h = self.drawer.draw_text(
                0,
                pos_y,
                font_size,
                line_str[0],
                self.config.fonts.font_console,
                anchor="lt",
            )
            pos_y += h - factor10_h
        if self.width > 450 and self.height > self.width:
            ohlc_image = makeCandle(
                self.price.ohlc,
                figsize_pixel=(self.width, self.height * 0.55),
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
        self.drawer.paste(ohlc_image, (0, pos_y))
        pos_y += ohlc_h
        if self.width > 450 and self.height > self.width:
            fs_low = self.drawer.calc_font_size(
                self.width,
                self.height - pos_y,
                line_str[6],
                self.config.fonts.font_buttom,
                anchor="rs",
            )
            w_low, h_low = self.drawer.draw_text(
                self.width - 1,
                self.height - 1,
                fs_low,
                line_str[6],
                self.config.fonts.font_buttom,
                anchor="rs",
            )
            w, h_symbolstring = self.drawer.drawText(
                factor5_w, self.height - h_low - factor10_h, line_str[5], self.font_side
            )

            self.rebuildFonts(side_size=34, fee_size=35)
            font_size = self.drawer.calc_font_size(
                self.width - factor5_w * 2,
                self.height - pos_y,
                line_str[2],
                self.config.fonts.font_fee,
                anchor="lt",
            )
            w, h = self.drawer.draw_text(
                factor5_w,
                pos_y,
                font_size,
                line_str[2],
                self.config.fonts.font_fee,
                anchor="lt",
            )
            pos_y += h

            w, h = self.drawer.drawText(factor5_w, pos_y, line_str[3], self.font_side)
            pos_y += h
            font_size = self.drawer.calc_font_size(
                self.width - factor5_w * 2,
                (self.height - factor20_h) / 2,
                line_str[4],
                self.config.fonts.font_side,
            )
            w, h = self.drawer.draw_text(
                factor5_w,
                self.height - h_low - h_symbolstring - factor20_h,
                font_size,
                line_str[4],
                self.config.fonts.font_side,
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
            pos_y = 0
            w, h = self.drawer.drawText(
                5,
                pos_y,
                '%s - %s - %s'
                % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
                self.font_top,
            )
            pos_y += h
            fees_string = self.get_fees_string(mempool)
            w, h = self.drawer.drawText(5, pos_y, fees_string, self.font_fee)
            pos_y += h
            w, h = self.drawer.drawText(
                5, pos_y, '%d blks %d txs' % (blocks, count), self.font_side
            )
            pos_y += h
            w, h = self.drawer.drawText(
                5,
                pos_y,
                '%d blk %.1f%% %s'
                % (
                    self.get_remaining_blocks(),
                    (retarget_mult * 100 - 100),
                    retarget_date.strftime("%d.%b%H:%M"),
                ),
                self.font_side,
            )
            pos_y += h
            font_size = self.drawer.calc_font_size(
                self.width,
                self.height - pos_y,
                self.get_current_block_height(),
                self.config.fonts.font_buttom,
                anchor="rs",
            )
            self.drawer.draw_text(
                self.width - 1,
                self.height - 1,
                font_size,
                self.get_current_block_height(),
                self.config.fonts.font_buttom,
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
                line_str[5] = ""
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
            pos_y = 0
            w, h = self.drawer.drawText(
                5,
                pos_y,
                '%s - %s - %s'
                % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
                self.font_top,
            )
            pos_y += h
            fees_string = self.get_fees_string(mempool)
            w, h = self.drawer.drawText(5, pos_y, fees_string, self.font_fee)
            pos_y += h
            w, h = self.drawer.drawText(
                5, pos_y, '%d blks %d txs' % (blocks, count), self.font_side
            )
            pos_y += h
            diff_string = self.get_next_difficulty_string(
                self.get_remaining_blocks(),
                retarget_mult,
                meanTimeDiff,
                time,
                retarget_date=retarget_date,
                show_clock=False,
            )
            w, h = self.drawer.drawText(5, 67, diff_string, self.font_side)
            pos_y += h
            fee_size = self.drawer.calc_font_size(
                self.width,
                self.height - pos_y,
                self.get_current_block_height(),
                self.config.fonts.font_buttom,
                anchor="rs",
            )
            self.drawer.draw_text(
                self.width - 1,
                self.height - 1,
                fee_size,
                self.get_current_block_height(),
                self.config.fonts.font_buttom,
                anchor="rs",
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
                line_str[6] = " "
                line_str[7] = format(int(current_price["usd"]), "")

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
        pricenowstring = self.price.getPriceNow()
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

        factor5_w = int(5 / 264 * self.width)
        factor3_h = int(3 / 176 * self.height)
        factor10_h = int(10 / 176 * self.height)
        factor15_h = int(15 / 176 * self.height)

        pos_y = factor3_h
        if line_str[0] != "":
            font_size = self.drawer.calc_font_size(
                self.width - factor5_w,
                (self.height - factor10_h),
                line_str[0] + " ",
                self.config.fonts.font_console,
                anchor="lt",
            )
            w, h = self.drawer.draw_text(
                factor5_w,
                pos_y,
                font_size,
                line_str[0] + " ",
                self.config.fonts.font_console,
                anchor="lt",
            )
            pos_y += h
        font_size = self.drawer.calc_font_size(
            self.width - factor5_w,
            self.height - pos_y - factor15_h,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        pos_y += h
        font_size = self.drawer.calc_font_size(
            self.width - 1,
            (self.height - pos_y - factor15_h),
            line_str[2],
            self.config.fonts.font_big,
            anchor="rs",
        )
        self.drawer.draw_text(
            self.width - 1,
            self.height - 1,
            font_size,
            line_str[2],
            self.config.fonts.font_big,
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

        factor5_w = int(5 / 264 * self.width)
        factor10_w = int(10 / 264 * self.width)
        factor20_w = int(20 / 264 * self.width)
        factor30_w = int(30 / 264 * self.width)
        factor40_w = int(40 / 264 * self.width)
        factor15_h = int(15 / 176 * self.height)
        factor50_h = int(50 / 176 * self.height)

        pos_y = factor30_w
        font_size = self.drawer.calc_font_size(
            self.width - factor10_w,
            factor50_h,
            line_str[1],
            self.config.fonts.font_fee,
            start_font_size=10,
            anchor="lb",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            self.height - factor15_h,
            font_size,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lb",
        )
        font_size = self.drawer.calc_font_size(
            self.width - factor40_w,
            (self.height - pos_y - h - factor15_h),
            line_str[0],
            self.config.fonts.font_big,
            anchor="rt",
        )
        self.drawer.draw_text(
            self.width - factor20_w,
            pos_y,
            font_size,
            line_str[0],
            self.config.fonts.font_big,
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

            line_str[1] = ""
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

        factor5_w = int(5 / 264 * self.width)
        factor3_h = int(3 / 176 * self.height)
        factor15_h = int(15 / 176 * self.height)
        factor50_h = int(50 / 176 * self.height)

        pos_y = factor3_h
        font_size = self.drawer.calc_font_size(
            self.width - factor5_w,
            self.height - factor50_h,
            line_str[0],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[0],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        pos_y += h
        # font_size = self.drawer.calc_font_size(
        #    self.width - factor5_w,
        #    self.height - pos_y - factor15_h,
        #    line_str[1],
        #    self.config.fonts.font_fee,
        #    anchor="lt",
        # )
        w, h = self.drawer.draw_text(
            factor5_w,
            pos_y,
            font_size,
            line_str[1],
            self.config.fonts.font_fee,
            anchor="lt",
        )
        pos_y += h
        font_size = self.drawer.calc_font_size(
            self.width - 1,
            (self.height - pos_y - factor15_h),
            line_str[2],
            self.config.fonts.font_big,
            anchor="rs",
        )
        self.drawer.draw_text(
            self.width - 1,
            self.height - 1,
            font_size,
            line_str[2],
            self.config.fonts.font_big,
            anchor="rs",
        )

    def get_image(self):
        return self.drawer.image

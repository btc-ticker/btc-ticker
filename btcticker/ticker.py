import math
import os
import time
from datetime import datetime

from babel import numbers
from btcpriceticker.price import Price
from piltext import FontManager, ImageDrawer, TextGrid

from btcticker.chart import makeCandle, makeSpark
from btcticker.config import Config
from btcticker.mempool import Mempool


class Ticker:
    def __init__(self, config: Config, width, height, days_ago=1):
        self.config = config
        self.height = height
        self.width = width
        self.fiat = config.main.fiat
        self.mempool = Mempool(api_url=config.main.mempool_api_url)
        self.price = Price(
            fiat=self.fiat,
            service=config.main.price_service,
            interval=config.main.interval,
            days_ago=days_ago,
            enable_ohlc=config.main.enable_ohlc,
        )
        self.mempool.request_timeout = 20

        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
        self.font_manager = FontManager(
            fontdir, default_font_size=20, default_font_name="Roboto-Medium"
        )
        self.image = ImageDrawer(width, height, self.font_manager)
        self.inverted = config.main.inverted
        self.orientation = config.main.orientation

    def get_line_str(self, sym):
        mempool = self.mempool.getData()
        symbolstring = numbers.get_currency_symbol(self.fiat.upper(), locale="en")
        current_price = self.price.price
        if sym == "empty":
            return ""
        if sym == "_current_block_height_":
            return str(mempool["height"])
        if sym == "_sat_per_fiat_with_symbol_":
            return "/{}{:.0f}".format(symbolstring, current_price["sat_fiat"])
        if sym == "_moscow_time_usd_":
            return "{:.0f}".format(current_price["sat_usd"])
        if sym == "_current_price_usd_":
            return format(int(current_price["usd"]), "")
        if sym == "_current_price_fiat_symbol_":
            pricenowstring = self.price.get_price_now()
            price_str = pricenowstring.replace(",", "")
            return symbolstring + price_str
        if sym == "_minutes_between_blocks_":
            return self.get_minutes_between_blocks()
        if sym == "_current_time_":
            return self.get_current_time()
        if sym == "_current_price_fiat_symbol_left_part_":
            pricenowstring = self.price.get_price_now()
            price_parts = pricenowstring.split(",")
            return self.get_symbol() + price_parts[0]
        if sym == "_current_price_fiat_symbol_right_part_":
            pricenowstring = self.price.get_price_now()
            price_parts = pricenowstring.split(",")
            return price_parts[1]
        return sym

    def generate_line_str(self, lines, mode):
        line_str = []
        line = ""
        for sym, value in lines[mode]:
            if sym == "n":
                line_str.append(line)
                line = ""
            elif sym == "t":
                if value != "":
                    line += value
                else:
                    line += " "
            elif sym == "s":
                line += self.get_line_str(value)
        if line != "":
            line_str.append(line)
        return line_str

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
            return "%d blk %.1f %% | %s -%d min" % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                self.get_last_block_time(date_and_time=False),
                int(last_block_sec_ago / 60),
            )
        elif retarget_date is not None:
            return "%d blk %.2f%% %s" % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                retarget_date.strftime("%d.%b %H:%M"),
            )
        else:
            return "%d blk %.0f %% %d:%d" % (
                remaining_blocks,
                (retarget_mult * 100 - 100),
                t_min,
                t_sec,
            )

    def get_fees_string(self, mempool):
        fee_str = "%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f"
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
        fee_str = "%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f"
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

        self.image.finalize(
            mirror=mirror,
            orientation=self.orientation,
            inverted=self.inverted,
        )

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
            price_str = "{:.0f}".format(current_price["sat_usd"])
        elif symbol == "sat_per_fiat":
            if with_symbol and shorten:
                price_str = "/{}{:.0f}".format(symbolstring, current_price["sat_fiat"])
            elif with_symbol and not shorten:
                price_str = "{:.0f} sat/{}".format(
                    current_price["sat_fiat"], symbolstring
                )
            else:
                price_str = "{:.0f}".format(current_price["sat_fiat"])
        elif symbol == "sat_per_usd":
            if shorten:
                price_str = "{:.0f} /$".format(current_price["sat_usd"])
            else:
                price_str = "{:.0f} sat/$".format(current_price["sat_usd"])

        return price_str

    def price_change_string(self, prefix_symbol: str | bool):
        pricechange = self.price.get_price_change()
        if prefix_symbol:
            return (
                prefix_symbol + "   " + str(self.price.days_ago) + "d : " + pricechange
            )
        else:
            return str(self.price.days_ago) + "day : " + pricechange

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
        return f"{int(t_min)}:{int(t_sec)}"

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
        return f"{int(last_block_sec_ago / 60)}:{last_block_sec_ago % 60} min"

    def get_current_time(self):
        return str(time.strftime("%H:%M"))

    def get_last_block_time3(self):
        mempool = self.mempool.getData()
        last_timestamp = mempool["last_block"]["timestamp"]
        last_block_time = datetime.fromtimestamp(last_timestamp)
        last_block_sec_ago = (datetime.now() - last_block_time).seconds
        return "%s (%d:%d min ago)" % (
            self.get_last_block_time(),
            int(last_block_sec_ago / 60),
            last_block_sec_ago % 60,
        )

    def generate_ohlc(self, mode):
        line_str = ["", "", "", "", "", "", ""]
        current_price = self.price.price
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
                + " - %.0f /%s - %.0f /$"
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = self.price_change_string(self.get_symbol())
            line_str[6] = self.get_current_price("fiat")
        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_price("fiat", with_symbol=True)
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                "$"
                + format(int(current_price["usd"]), "")
                + " - %.0f /%s - %.0f /$"
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = self.price_change_string("")
            line_str[6] = self.get_current_block_height()
        elif mode == "satfiat":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + " - $"
                + format(int(current_price["usd"]), "")
                + " - %.0f /$" % (current_price["sat_usd"])
            )
            line_str[5] = self.price_change_string("/%s" % self.get_symbol())
            line_str[6] = self.get_current_price("sat_per_fiat")
        elif mode == "moscowtime":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + " - $"
                + format(int(current_price["usd"]), "")
                + f" - {self.get_sat_per_fiat():.0f} /{self.get_symbol()}"
            )
            line_str[5] = self.price_change_string("/$")
            line_str[6] = "%.0f" % current_price["sat_usd"]
        elif mode == "usd":
            line_str[0] = self.get_current_block_height()
            line_str[1] = self.get_last_block_time3()
            line_str[4] = (
                self.get_symbol()
                + self.get_current_price("fiat")
                + " - %.0f /%s - %.0f /$"
                % (
                    self.get_sat_per_fiat(),
                    self.get_symbol(),
                    current_price["sat_usd"],
                )
            )
            line_str[5] = self.price_change_string("$")
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
        return line_str

    def draw_ohlc(self, mode):
        line_str = self.generate_ohlc(mode)
        w = 6
        dpi = int(480 / w)

        if self.width > 450 and self.height > self.width:
            grid = TextGrid(35, 6, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (2, 5))
            grid.merge((3, 0), (4, 5))
            grid.merge((5, 0), (20, 5))
            grid.merge((21, 0), (22, 5))
            grid.merge((23, 0), (24, 5))
            grid.merge((25, 0), (26, 5))
            grid.merge((27, 0), (28, 5))
            grid.merge((29, 0), (34, 5))
            start_img, end_img = grid.get_grid((5, 0), convert_to_pixel=True)
            ohlc_image = makeCandle(
                self.price.ohlc,
                figsize_pixel=(end_img[0] - start_img[0], end_img[1] - start_img[1]),
                dpi=dpi,
                x_axis=False,
            )

            grid.set_text((0, 0), line_str[0], font_name=self.config.fonts.font_console)
            grid.set_text((3, 0), line_str[1], font_name=self.config.fonts.font_side)
            grid.paste_image((5, 0), ohlc_image, anchor="rs")
            grid.set_text((21, 0), line_str[2], font_name=self.config.fonts.font_fee)
            grid.set_text((23, 0), line_str[3], font_name=self.config.fonts.font_side)
            grid.set_text((25, 0), line_str[4], font_name=self.config.fonts.font_side)
            grid.set_text((27, 0), line_str[5], font_name=self.config.fonts.font_side)
            grid.set_text(
                (29, 0),
                line_str[6],
                font_name=self.config.fonts.font_buttom,
                anchor="rs",
            )
        else:
            grid = TextGrid(21, 6, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (4, 5))
            grid.merge((5, 0), (20, 5))
            start_img, end_img = grid.get_grid((5, 0), convert_to_pixel=True)
            ohlc_image = makeCandle(
                self.price.ohlc,
                figsize_pixel=(end_img[0] - start_img[0], end_img[1] - start_img[1]),
                dpi=dpi,
                x_axis=False,
            )

            grid.set_text((0, 0), line_str[0], font_name=self.config.fonts.font_console)
            grid.paste_image((5, 0), ohlc_image, anchor="rs")

    def generate_all(self, mode):
        line_str = [" ", " ", " ", " ", " ", " ", " ", " "]
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
            line_str[0] = "%s - %s - %s" % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[1] = self.get_fees_string(mempool)
            line_str[2] = "%d blks %d txs" % (blocks, count)
            line_str[3] = "%d blk %.1f%% %s" % (
                self.get_remaining_blocks(),
                (retarget_mult * 100 - 100),
                retarget_date.strftime("%d.%b%H:%M"),
            )
            line_str[4] = self.get_current_block_height()

        else:
            if mode == "fiat":
                if self.config.main.show_block_time:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                else:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )

                line_str[2] = "$%.0f" % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = self.get_symbol() + " "

                line_str[7] = self.get_current_price("fiat")
            elif mode == "height":
                if not self.config.main.show_block_time:
                    line_str[0] = "{} - {} - {}".format(
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "$%.0f" % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                # line_str[5] = ""
                line_str[7] = self.get_current_block_height()
            elif mode == "satfiat":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "$%.0f" % current_price["usd"]
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/%s " % self.get_symbol()
                line_str[7] = self.get_current_price("sat_per_fiat")
            elif mode == "moscowtime":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = self.get_current_price("usd", with_symbol=True)
                line_str[3] = self.get_current_price(
                    "sat_per_fiat", with_symbol=True, shorten=False
                )
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat/$"
                line_str[6] = " "
                line_str[7] = self.get_current_price("moscow_time_usd")
            elif mode == "usd":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = self.get_current_price("fiat", with_symbol=True)
                line_str[3] = self.get_current_price("sat_per_usd")
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = "$ "
                line_str[6] = " "
                line_str[7] = format(int(current_price["usd"]), "")

            line_str[1] = self.get_fees_string(mempool)

            line_str[6] = self.price_change_string(False)
        return line_str

    def draw_all(self, mode):
        line_str = self.generate_all(mode)
        pricestack = self.price.get_timeseries_list()
        if mode == "newblock":
            grid = TextGrid(8, 4, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (1, 3))
            grid.merge((2, 0), (2, 3))
            grid.merge((3, 0), (3, 3))
            grid.merge((4, 0), (4, 3))
            grid.merge((5, 0), (7, 3))
            grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
            grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)
            grid.set_text(2, line_str[2], font_name=self.config.fonts.font_side)
            grid.set_text(3, line_str[3], font_name=self.config.fonts.font_side)
            grid.set_text(
                4, line_str[4], font_name=self.config.fonts.font_buttom, anchor="rs"
            )
        else:
            grid = TextGrid(21, 6, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (2, 5))
            grid.merge((3, 0), (4, 5))
            grid.merge((5, 2), (10, 5))
            grid.merge((5, 0), (6, 1))
            grid.merge((7, 0), (8, 1))
            grid.merge((9, 0), (10, 1))
            grid.merge((11, 0), (12, 1))
            grid.merge((11, 3), (12, 5))
            grid.merge((13, 0), (20, 5))
            start_img, end_img = grid.get_grid((5, 2), convert_to_pixel=True)
            spark_image = makeSpark(
                pricestack,
                figsize_pixel=(end_img[0] - start_img[0], end_img[1] - start_img[1]),
            )

            grid.set_text((0, 0), line_str[0], font_name=self.config.fonts.font_top)
            grid.set_text((3, 0), line_str[1], font_name=self.config.fonts.font_fee)
            grid.paste_image((5, 2), spark_image, anchor="rs")
            grid.set_text((5, 0), line_str[2], font_name=self.config.fonts.font_side)
            grid.set_text((7, 0), line_str[3], font_name=self.config.fonts.font_side)
            grid.set_text((9, 0), line_str[4], font_name=self.config.fonts.font_side)
            grid.set_text((11, 0), line_str[5], font_name=self.config.fonts.font_side)
            grid.set_text((11, 3), line_str[6], font_name=self.config.fonts.font_fee)
            grid.set_text(
                (13, 0),
                line_str[7],
                font_name=self.config.fonts.font_buttom,
                anchor="rs",
            )

    def generate_fiat(self, mode):
        line_str = [" ", " ", " ", " ", " ", " ", " ", " "]
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
            line_str[0] = "%s - %s - %s" % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_minutes_between_blocks(),
                self.get_current_time(),
            )
            line_str[1] = self.get_fees_string(mempool)
            line_str[2] = "%d blks %d txs" % (blocks, count)
            line_str[3] = self.get_next_difficulty_string(
                self.get_remaining_blocks(),
                retarget_mult,
                meanTimeDiff,
                time,
                retarget_date=retarget_date,
                show_clock=False,
            )
            line_str[4] = self.get_current_block_height()

        else:
            if mode == "fiat":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "lb -%d:%d" % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = "%d blk" % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = self.get_symbol()
                line_str[6] = " "
                line_str[7] = self.get_current_price("fiat")
            elif mode == "height":
                if not self.config.main.show_block_time:
                    line_str[0] = "{} - {} - {}".format(
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_minutes_between_blocks(),
                        self.get_current_time(),
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_price("fiat", with_symbol=True),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "lb -%d:%d" % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = "%d blk" % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("sat_per_fiat", with_symbol=True)
                line_str[5] = " "
                line_str[6] = " "
                line_str[7] = self.get_current_block_height()
            elif mode == "satfiat":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "lb -%d:%d" % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = "%d blk" % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat/%s" % self.get_symbol()
                line_str[6] = " "
                line_str[7] = self.get_current_price("sat_per_fiat")
            elif mode == "moscowtime":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "lb -%d:%d" % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = "%d blk" % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "sat"
                line_str[6] = "/$"
                line_str[7] = self.get_current_price("moscow_time_usd")
            elif mode == "usd":
                if not self.config.main.show_block_time:
                    line_str[0] = (
                        f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}"
                    )
                else:
                    line_str[0] = "%s-%s-%d min" % (
                        self.get_current_block_height(),
                        self.get_last_block_time(date_and_time=False),
                        int(last_block_sec_ago / 60),
                    )
                line_str[2] = "lb -%d:%d" % (
                    int(last_block_sec_ago / 60),
                    last_block_sec_ago % 60,
                )
                line_str[3] = "%d blk" % (self.get_remaining_blocks())
                line_str[4] = self.get_current_price("fiat", with_symbol=True)
                line_str[5] = "$"
                line_str[6] = format(int(current_price["usd"]), "")
                line_str[7] = self.get_current_price("usd")

            line_str[1] = self.get_fees_string(mempool)

            line_str[6] = self.price_change_string(False)
        return line_str

    def draw_fiat(self, mode):
        pricestack = self.price.get_timeseries_list()
        line_str = self.generate_fiat(mode)
        if mode == "newblock":
            grid = TextGrid(8, 4, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (1, 3))
            grid.merge((2, 0), (2, 3))
            grid.merge((3, 0), (3, 3))
            grid.merge((4, 0), (4, 3))
            grid.merge((5, 0), (7, 3))
            grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
            grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)
            grid.set_text(2, line_str[2], font_name=self.config.fonts.font_side)
            grid.set_text(3, line_str[3], font_name=self.config.fonts.font_side)
            grid.set_text(
                4, line_str[4], font_name=self.config.fonts.font_buttom, anchor="rs"
            )
        else:
            grid = TextGrid(22, 6, self.image, margin_x=1, margin_y=1)
            grid.merge((0, 0), (2, 5))
            grid.merge((3, 0), (4, 5))
            grid.merge((5, 2), (10, 5))
            grid.merge((5, 0), (6, 1))
            grid.merge((7, 0), (8, 1))
            grid.merge((9, 0), (10, 1))
            grid.merge((11, 0), (12, 1))
            grid.merge((11, 3), (12, 5))
            grid.merge((13, 0), (21, 5))
            start_img, end_img = grid.get_grid((5, 2), convert_to_pixel=True)
            spark_image = makeSpark(
                pricestack,
                figsize_pixel=(end_img[0] - start_img[0], end_img[1] - start_img[1]),
            )

            grid.set_text((0, 0), line_str[0], font_name=self.config.fonts.font_top)
            grid.set_text((3, 0), line_str[1], font_name=self.config.fonts.font_fee)
            grid.paste_image((5, 2), spark_image, anchor="rs")
            grid.set_text((5, 0), line_str[2], font_name=self.config.fonts.font_side)
            grid.set_text((7, 0), line_str[3], font_name=self.config.fonts.font_side)
            grid.set_text((9, 0), line_str[4], font_name=self.config.fonts.font_side)
            grid.set_text((11, 0), line_str[5], font_name=self.config.fonts.font_side)
            grid.set_text((11, 3), line_str[6], font_name=self.config.fonts.font_fee)
            grid.set_text(
                (13, 0),
                line_str[7],
                font_name=self.config.fonts.font_buttom,
                anchor="rs",
            )

    def generate_fiat_height(self, mode):
        line_str = ["", "", "", "", ""]
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
                line_str[3] = "{:.0f} /{} - ${} - {:.0f} /$".format(
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
                line_str[3] = "{:.0f} /{} - ${} - {:.0f} /$".format(
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
                line_str[3] = "{} - ${} - {:.0f} /$".format(
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
                line_str[3] = "{} - ${} - {:.0f} /$".format(
                    self.get_current_price("fiat", with_symbol=True),
                    format(int(current_price["usd"]), ""),
                    current_price["sat_usd"],
                )
            line_str[4] = "/$%.0f" % (current_price["sat_usd"])
        elif mode == "usd":
            line_str[0] = self.get_current_block_height()
            if self.config.main.fiat == "usd":
                line_str[3] = self.get_current_price("sat_per_fiat", with_symbol=True)
            else:
                line_str[3] = "{:.0f} /{} - {} - {:.0f} /$".format(
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
        return line_str

    def draw_fiat_height(self, mode):
        line_str = self.generate_fiat_height(mode)
        grid = TextGrid(8, 4, self.image, margin_x=1, margin_y=1)
        grid.merge((0, 0), (1, 3))
        grid.merge((2, 0), (2, 3))
        grid.merge((3, 0), (3, 3))
        grid.merge((4, 0), (4, 3))
        grid.merge((5, 0), (7, 3))
        grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
        grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)
        grid.set_text(2, line_str[2], font_name=self.config.fonts.font_side)
        grid.set_text(3, line_str[3], font_name=self.config.fonts.font_side)
        grid.set_text(
            4, line_str[4], font_name=self.config.fonts.font_buttom, anchor="rs"
        )

    def generate_mempool(self, mode):
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
        line_str = ["", "", "", ""]
        if mode == "fiat":
            line_str[0] = self.get_current_price("fiat")
            line_str[2] = "%s - %.0f /%s - lb -%d:%d" % (
                self.get_current_block_height(),
                self.get_sat_per_fiat(),
                self.get_symbol(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "height" or mode == "newblock":
            line_str[0] = self.get_current_block_height()
            line_str[2] = "%s - %.0f /%s - lb -%d:%d" % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_sat_per_fiat(),
                self.get_symbol(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "satfiat":
            line_str[0] = self.get_current_price("sat_per_fiat", with_symbol=True)
            line_str[2] = "%s - %s - lb -%d:%d" % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_current_block_height(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "moscowtime":
            line_str[0] = self.get_current_price("sat_per_usd", shorten=True)
            line_str[2] = "%s - %s - lb -%d:%d" % (
                self.get_current_price("fiat", with_symbol=True),
                self.get_current_block_height(),
                int(last_block_sec_ago / 60),
                last_block_sec_ago % 60,
            )

        elif mode == "usd":
            line_str[0] = self.get_current_price("usd")
            line_str[2] = "%s - %s - lb -%d:%d" % (
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
        return line_str

    def draw_mempool(self, mode):
        line_str = self.generate_mempool(mode)
        grid = TextGrid(7, 4, self.image, margin_x=1, margin_y=1)
        grid.merge((0, 0), (1, 3))
        grid.merge((2, 0), (2, 3))
        grid.merge((3, 0), (3, 3))
        grid.merge((4, 0), (6, 3))
        grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
        grid.set_text(1, line_str[1], font_name=self.config.fonts.font_side)
        grid.set_text(2, line_str[2], font_name=self.config.fonts.font_side)
        grid.set_text(3, line_str[3], font_name=self.config.fonts.font_big, anchor="rs")

    def generate_big_two_rows(self, mode):
        current_price = self.price.price
        pricenowstring = self.price.get_price_now()
        price_parts = pricenowstring.split(",")
        lines = {}
        price_parts = pricenowstring.split(",")
        price_parts_usd = format(int(current_price["usd"]), ",").split(",")
        lines["fiat"] = [
            ("t", self.get_symbol() + price_parts[0]),
            ("n", ""),
            (
                "t",
                f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}",
            ),
            ("n", ""),
            ("t", price_parts[1]),
        ]
        lines["height"] = [
            ("t", self.get_current_block_height()[:3]),
            ("n", ""),
            (
                "t",
                f"{self.get_symbol() + pricenowstring} - {self.get_minutes_between_blocks()} - {self.get_current_time()}",
            ),
            ("n", ""),
            ("t", self.get_current_block_height()[3:]),
        ]
        lines["newblock"] = lines["height"]
        lines["satfiat"] = [
            ("t", f"sat/{self.get_symbol()}"),
            ("n", ""),
            (
                "t",
                f"{self.get_symbol() + pricenowstring} - {self.get_minutes_between_blocks()} - {self.get_current_time()}",
            ),
            ("n", ""),
            ("t", self.get_current_price("sat_per_fiat")),
        ]
        lines["moscowtime"] = [
            ("t", "sat/$"),
            ("n", ""),
            (
                "t",
                f"{self.get_symbol() + pricenowstring} - {self.get_minutes_between_blocks()} - {self.get_current_time()}",
            ),
            ("n", ""),
            ("t", self.get_current_price("moscow_time_usd")),
        ]
        lines["usd"] = [
            ("t", "$" + price_parts_usd[0]),
            ("n", ""),
            (
                "t",
                f"{self.get_current_block_height()} - {self.get_minutes_between_blocks()} - {self.get_current_time()}",
            ),
            ("n", ""),
            ("t", price_parts[1]),
        ]

        return self.generate_line_str(lines, mode)

    def draw_big_two_rows(self, mode):
        line_str = self.generate_big_two_rows(mode)
        grid = TextGrid(9, 4, self.image, margin_x=1, margin_y=1)
        grid.merge((0, 0), (3, 3))
        grid.merge((4, 0), (4, 3))
        grid.merge((5, 0), (8, 3))
        grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
        grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)
        grid.set_text(
            2, line_str[2], font_name=self.config.fonts.font_console, anchor="rs"
        )

    def generate_one_number(self, mode):
        lines = {}
        lines["fiat"] = [
            ("s", "_current_price_fiat_symbol_"),
            ("n", ""),
            ("t", "Market price of bitcoin"),
        ]
        lines["height"] = [
            ("s", "_current_block_height_"),
            ("n", ""),
            ("t", "Number of blocks in the blockchain"),
        ]
        lines["newblock"] = [
            ("s", "_current_block_height_"),
            ("n", ""),
            ("t", "Number of blocks in the blockchain"),
        ]
        lines["satfiat"] = [
            ("s", "_sat_per_fiat_with_symbol_"),
            ("n", ""),
            ("t", f"Value of one {self.get_symbol()} in sats"),
        ]
        lines["moscowtime"] = [
            ("s", "_moscow_time_usd_"),
            ("n", ""),
            ("t", "moscow time"),
        ]
        lines["usd"] = [
            ("s", "_current_price_usd_"),
            ("n", ""),
            ("t", "Market price of bitcoin"),
        ]
        return self.generate_line_str(lines, mode)

    def draw_one_number(self, mode):
        line_str = self.generate_one_number(mode)
        grid = TextGrid(8, 4, self.image, margin_x=10, margin_y=10)
        grid.merge((2, 0), (4, 3))
        grid.merge((5, 0), (7, 3))
        grid.set_text(0, line_str[0], font_name=self.config.fonts.font_fee)
        grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)

    def generate_big_one_row(self, mode):
        mempool = self.mempool.getData()
        lines = {}

        lines["fiat"] = [
            (
                "t",
                "%s - %d - %s - %s"  # noqa: UP031
                % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
            ),
            ("n", ""),
            ("t", self.get_symbol() + " " + self.get_fee_string(mempool)),
            ("n", ""),
            ("t", self.get_current_price("fiat")),
        ]
        lines["height"] = [
            (
                "t",
                "%s - %d - %s - %s"
                % (
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
            ),
            ("n", ""),
            ("t", self.get_fee_string(mempool)),
            ("n", ""),
            ("t", self.get_current_block_height()),
        ]
        lines["satfiat"] = [
            (
                "t",
                "%s - %d - %s - %s"
                % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
            ),
            ("n", ""),
            ("t", "/%s" % self.get_symbol() + " " + self.get_fee_string(mempool)),
            ("n", ""),
            ("t", self.get_current_price("sat_per_fiat")),
        ]
        lines["moscowtime"] = [
            (
                "t",
                "%s - %d - %s - %s"
                % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
            ),
            ("n", ""),
            ("t", "/$ " + self.get_fee_string(mempool)),
            ("n", ""),
            ("t", self.get_current_price("sat_per_fiat")),
        ]
        lines["usd"] = [
            (
                "t",
                "%s - %d - %s - %s"
                % (
                    self.get_current_block_height(),
                    self.get_remaining_blocks(),
                    self.get_minutes_between_blocks(),
                    self.get_current_time(),
                ),
            ),
            ("n", ""),
            ("t", "$ " + self.get_fee_string(mempool)),
            ("n", ""),
            ("t", self.get_current_price("usd")),
        ]

        # line_str[1] = self.get_fee_string(mempool)

        if self.config.main.show_block_time:
            lines["fiat"][0] = (
                "t",
                f"{self.get_current_block_height()} - {self.get_last_block_time()} - {self.get_last_block_time2()}",
            )
            lines["height"][0] = (
                "t",
                "{} - {} - {}".format(
                    self.get_current_price("fiat", with_symbol=True),
                    self.get_last_block_time(),
                    self.get_last_block_time2(),
                ),
            )
            lines["satfiat"][0] = (
                "t",
                f"{self.get_current_block_height()} - {self.get_last_block_time()} - {self.get_last_block_time2()}",
            )
            lines["moscowtime"][0] = (
                "t",
                f"{self.get_current_block_height()} - {self.get_last_block_time()} - {self.get_last_block_time2()}",
            )
            lines["usd"][0] = (
                "t",
                f"{self.get_current_block_height()} - {self.get_last_block_time()} - {self.get_last_block_time2()}",
            )

        lines["newblock"] = lines["height"]
        return self.generate_line_str(lines, mode)

    def draw_big_one_row(self, mode):
        line_str = self.generate_big_one_row(mode)
        grid = TextGrid(9, 4, self.image, margin_x=1, margin_y=1)
        grid.merge((0, 0), (0, 3))
        grid.merge((1, 0), (1, 3))
        grid.merge((2, 0), (8, 3))
        grid.set_text(0, line_str[0], font_name=self.config.fonts.font_console)
        grid.set_text(1, line_str[1], font_name=self.config.fonts.font_fee)
        grid.set_text(2, line_str[2], font_name=self.config.fonts.font_big, anchor="rs")

    def get_image(self):
        return self.image.image_handler.image

import io
import logging
import time

import PySimpleGUI as sg
import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from btcticker.config import Config
from btcticker.ticker import Ticker

logger = logging.getLogger(__name__)
console = Console()


def get_display_size(epd_type="2in7_4gray"):
    if epd_type == "2in7":
        return 176, 264
    elif epd_type == "2in7_V2":
        return 176, 264
    elif epd_type == "2in7_4gray":
        return 176, 264
    elif epd_type == "2in9_V2":
        return 128, 296
    elif epd_type == "7in5_V2":
        return 480, 800
    else:
        return 528, 880


def get_img_data(img):
    """Generate image data using PIL."""
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()


def main(
    layout_ind: int = typer.Argument(default=0),
    mode_ind: int = typer.Argument(default=0),
    days: int = typer.Argument(default=1),
):
    layout_list = [
        "all",
        "fiat",
        "fiatheight",
        "big_one_row",
        "big_two_rows",
        "one_number",
        "mempool",
        "ohlc",
    ]
    mode_list = ["fiat", "height", "satfiat", "usd", "newblock", "moscowtime"]
    layout = layout_list[layout_ind]
    mode = mode_list[mode_ind]
    config = Config("home.admin/config.ini")
    config.main.epd_type = "7in5_V2"
    h, w = get_display_size(epd_type=config.main.epd_type)
    config.main.enable_ohlc = False
    config.main.price_service = "coinpaprika"
    config.main.interval = "1h"
    config.main.orientation = 90

    if config.main.orientation == 90:
        ticker = Ticker(config, h, w)
    elif config.main.orientation == 270:
        ticker = Ticker(config, h, w)
    else:
        ticker = Ticker(config, w, h)

    ticker.set_days_ago(days)
    ticker.refresh()

    line_str = []
    if layout == "all":
        line_str = ticker.generate_all(mode)
    elif layout == "fiat":
        line_str = ticker.generate_fiat(mode)
    elif layout == "fiatheight":
        line_str = ticker.generate_fiat_height(mode)
    elif layout == "big_one_row":
        line_str = ticker.generate_big_one_row(mode)
    elif layout == "big_two_rows":
        line_str = ticker.generate_big_two_rows(mode)
    elif layout == "one_number":
        line_str = ticker.generate_one_number(mode)
    elif layout == "mempool":
        line_str = ticker.generate_mempool(mode)
    elif layout == "ohlc":
        line_str = ticker.generate_ohlc(mode)
    table = Table("Index", f"{layout} - {mode}")
    index = 0
    for line in line_str:
        table.add_row(f"{index}", line)
        index += 1
    console.print(table)


if __name__ == "__main__":
    typer.run(main)

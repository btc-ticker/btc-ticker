import io
import logging
from io import BytesIO

import typer
from libsixel import (
    SIXEL_BUILTIN_G1,
    SIXEL_BUILTIN_G8,
    SIXEL_PIXELFORMAT_G1,
    SIXEL_PIXELFORMAT_G8,
    SIXEL_PIXELFORMAT_PAL8,
    SIXEL_PIXELFORMAT_RGB888,
    SIXEL_PIXELFORMAT_RGBA8888,
    sixel_dither_get,
    sixel_dither_initialize,
    sixel_dither_new,
    sixel_dither_set_palette,
    sixel_dither_set_pixelformat,
    sixel_dither_unref,
    sixel_encode,
    sixel_output_new,
    sixel_output_unref,
)
from rich.console import Console

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
    orientation: int = typer.Argument(default=0),
    epd_type: str = typer.Argument(default="2in7_V2"),
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
    config.main.epd_type = epd_type
    h, w = get_display_size(epd_type=config.main.epd_type)
    if layout == "ohlc":
        config.main.enable_ohlc = True
        config.main.price_service = "coingecko"
    else:
        config.main.enable_ohlc = False
        config.main.price_service = "coinpaprika"
    config.main.interval = "1h"
    config.main.orientation = orientation

    if config.main.orientation == 90:
        ticker = Ticker(config, h, w)
    elif config.main.orientation == 270:
        ticker = Ticker(config, h, w)
    else:
        ticker = Ticker(config, w, h)

    ticker.set_days_ago(days)
    ticker.refresh()

    s = BytesIO()
    print(
        f"Creating image for h: {h}, w: {w}, o: {ticker.orientation} "
        f"with mode: {mode} layout: {layout}"
    )
    ticker.build(mirror=False, mode=mode, layout=layout)
    image = ticker.get_image()
    width, height = image.size
    try:
        data = image.tobytes()
    except NotImplementedError:
        data = image.tostring()
    output = sixel_output_new(lambda data, s: s.write(data), s)

    try:
        if image.mode == "RGBA":
            dither = sixel_dither_new(256)
            sixel_dither_initialize(
                dither, data, width, height, SIXEL_PIXELFORMAT_RGBA8888
            )
        elif image.mode == "RGB":
            dither = sixel_dither_new(256)
            sixel_dither_initialize(
                dither, data, width, height, SIXEL_PIXELFORMAT_RGB888
            )
        elif image.mode == "P":
            palette = image.getpalette()
            dither = sixel_dither_new(256)
            sixel_dither_set_palette(dither, palette)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_PAL8)
        elif image.mode == "L":
            dither = sixel_dither_get(SIXEL_BUILTIN_G8)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G8)
        elif image.mode == "1":
            dither = sixel_dither_get(SIXEL_BUILTIN_G1)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G1)
        else:
            raise RuntimeError("unexpected image mode")
        try:
            sixel_encode(data, width, height, 1, dither, output)
            print(s.getvalue().decode("ascii"))
        finally:
            sixel_dither_unref(dither)
    finally:
        sixel_output_unref(output)


if __name__ == "__main__":
    typer.run(main)

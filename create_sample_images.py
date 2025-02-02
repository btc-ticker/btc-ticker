import logging

from btcticker.config import Config
from btcticker.ticker import Ticker

logger = logging.getLogger(__name__)


config = Config("home.admin/config.ini")

w = 176
h = 264

ticker = Ticker(config, w, h)
# ticker.price.enable_ohlc = True
ticker.price.enable_ohlc = False
# ticker.orientation = 0

ticker.set_days_ago(3)
ticker.refresh()

mode_list = "fiat,height,satfiat,moscowtime,usd".split(",")
layout_list = "all,fiat,fiatheight,big_one_row,one_number,big_two_rows,mempool".split(
    ","
)
# layout_list = ["big_one_row"]
# layout_list = ["one_number"]
# layout_list = ["big_two_rows"]
# layout_list = ["mempool"]
# layout_list = ["fiatheight"]
# layout_list = ["fiat"]
# layout_list = ["all"]
# layout_list = ["mempool"]
# layout_list = ["ohlc"]
size_list = [
    # (122, 250, 0),
    (176, 264, 0),
    # (128, 296, 0),
    (280, 480, 0),
    # (480, 800, 0),
    # (800, 480, 0),
]

for h, w, o in size_list:
    ticker.change_size(w, h)
    ticker.orientation = o
    for layout in layout_list:
        for mode in mode_list:
            print(
                f"Creating image for h: {h}, w: {w}, o: {o} with mode: {mode} layout: {layout}"
            )
            ticker.build(mirror=False, mode=mode, layout=layout)
            ticker.get_image().save(
                f"./sample_images/{w}_{h}_{o}_{mode}_{layout}.PNG", format="PNG"
            )

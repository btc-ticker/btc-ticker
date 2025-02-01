import io
import logging
import time

import PySimpleGUI as sg

from btcticker.config import Config
from btcticker.ticker import Ticker

logger = logging.getLogger(__name__)


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


config = Config("home.admin/config.ini")

h, w = get_display_size(epd_type=config.main.epd_type)

if config.main.orientation == 90:
    ticker = Ticker(config, h, w)
elif config.main.orientation == 270:
    ticker = Ticker(config, h, w)
else:
    ticker = Ticker(config, w, h)
ticker.orientation = 0

mode_list = ["fiat", "height", "satfiat", "usd", "newblock"]
# mode_list = []
for mode in config.main.mode_list.split(","):
    mode_list.append(mode.replace('"', "").replace(" ", ""))
ticker_ind = 0 #config.main.start_mode_ind
mode_shifting = True #config.main.mode_shifting

days_list = []
for d in config.main.days_list.split(","):
    days_list.append(int(d.replace('"', '').replace(" ", "")))
days_ind = config.main.start_days_ind
days_shifting = config.main.days_shifting

layout_list = ["all","fiat","fiatheight","big_one_row","one_number","mempool","ohlc"]
for layout in config.main.layout_list.split(","):
    layout_list.append(layout.replace('"', "").replace(" ", ""))
layout_ind = 5 #config.main.start_layout_ind
layout_shifting = False #config.main.layout_shifting

ticker.set_days_ago(days_list[days_ind])
ticker.refresh()
ticker.build(mirror=False, mode=mode_list[ticker_ind], layout=layout_list[layout_ind])
ticker.set_min_refresh_time(120)

image_elem = sg.Image(data=get_img_data(ticker.get_image()))

col = [[image_elem]]


layout = [[sg.Column(col)]]

window = sg.Window(
    'BTC Ticker',
    layout,
    return_keyboard_events=True,
    location=(0, 0),
    use_default_focus=False,
)

# loop reading the user input and displaying image, filename
i = 0

while True:
    # read the form
    event, values = window.read(timeout=3000)
    # perform button and keyboard operations
    if event == sg.WIN_CLOSED:
        break
    elif event == sg.TIMEOUT_EVENT:
        ticker_ind += 1
        if ticker_ind >= len(mode_list) or not mode_shifting:
            ticker_ind = 0
            layout_ind += 1
            if layout_ind >= len(layout_list) or not layout_shifting:
                layout_ind = 0
                days_ind += 1
                if days_ind >= len(days_list) or not days_shifting:
                    days_ind = 0
                    
        print(f"Running loop with mode: {mode_list[ticker_ind]} layout: {layout_list[layout_ind]}")
        ticker.set_days_ago(days_list[days_ind])
        ticker.refresh()
        ticker.build(
            mirror=False, mode=mode_list[ticker_ind], layout=layout_list[layout_ind]
        )
        # update window with new image
        image_elem.update(data=get_img_data(ticker.get_image()))
        time.sleep(2)


window.close()

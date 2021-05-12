import PySimpleGUI as sg
from btcticker.ticker import Ticker
from btcticker.config import Config
import os
from PIL import Image, ImageTk
import io
import time


def get_display_size(epd_type="2in7"):
    if epd_type == "2in7":
        return 176, 264
    else:
        return 528, 880


def get_img_data(img):
    """Generate image data using PIL
    """
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

config = Config("home.admin/config.ini")

w, h = get_display_size(epd_type=config.main.epd_type)

ticker = Ticker(config, w, h)

# ticker_mode = ["fiat", "height", "satfiat", "usd", "newblock"]
mode_list = []
for l in config.main.mode_list.split(","):
    mode_list.append(l.replace('"', "").replace(" ", ""))
ticker_ind = config.main.start_mode_ind

days_list = []
for d in config.main.days_list.split(","):
    days_list.append(int(d.replace('"', '').replace(" ", "")))
layout_list = []
for l in config.main.layout_list.split(","):
    layout_list.append(l.replace('"', "").replace(" ", ""))
layout_ind = config.main.start_layout_ind
ticker.refresh()
ticker.build(mirror=False, mode=mode_list[ticker_ind], layout=layout_list[layout_ind])



image_elem = sg.Image(data=get_img_data(ticker.image))

col = [[image_elem]]


layout = [[sg.Column(col)]]

window = sg.Window('BTC Ticker', layout, return_keyboard_events=True,
                   location=(0, 0), use_default_focus=False)

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
        if ticker_ind >= len(mode_list):
            ticker_ind = 0
            layout_ind += 1
            if layout_ind >= len(layout_list):
                layout_ind = 0
        ticker.build(mirror=False, mode=mode_list[ticker_ind], layout=layout_list[layout_ind])

        # update window with new image
        image_elem.update(data=get_img_data(ticker.image))


window.close()
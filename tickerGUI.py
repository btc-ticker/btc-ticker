import PySimpleGUI as sg
from btcticker.ticker import Ticker
from btcticker.config import Config
import os
from PIL import Image, ImageTk
import io
import time


def get_img_data(img):
    """Generate image data using PIL
    """
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

config = Config("home.admin/config.ini")
ticker = Ticker(config)
ticker_mode = ["fiat", "height", "satfiat", "usd", "newblock"]
ticker_ind = 2
ticker.update(mirror=False, mode=ticker_mode[ticker_ind])



image_elem = sg.Image(data=get_img_data(ticker.image))

col = [[image_elem]]


layout = [[sg.Column(col)]]

window = sg.Window('BTC Ticker', layout, return_keyboard_events=True,
                   location=(0, 0), use_default_focus=False)

# loop reading the user input and displaying image, filename
i = 0
while True:
    # read the form
    event, values = window.read(timeout=30000)
    # perform button and keyboard operations
    if event == sg.WIN_CLOSED:
        break
    elif event == sg.TIMEOUT_EVENT:
        ticker_ind += 1
        if ticker_ind >= len(ticker_mode):
            ticker_ind = 0        
        ticker.update(mirror=False, mode=ticker_mode[ticker_ind])

        # update window with new image
        image_elem.update(data=get_img_data(ticker.image))


window.close()
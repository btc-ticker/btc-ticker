import PySimpleGUI as sg
from btcticker.ticker import Ticker
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

ticker = Ticker()
ticker_mode = "newblock"
ticker.update(mirror=False, mode=ticker_mode)



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
        ticker.update(mirror=False, mode=ticker_mode)
        # update window with new image
        image_elem.update(data=get_img_data(ticker.image))


window.close()
#!/usr/bin/python3
import argparse
import atexit
import http.client as httplib
import logging
import logging.handlers
import os
import signal
import socket
import sys
import tempfile
import time

import RPi.GPIO as GPIO
import sdnotify
from PIL import Image

from btcticker.config import Config
from btcticker.epd import get_epd
from btcticker.ticker import Ticker

temp_dir = tempfile.TemporaryDirectory()
os.environ['MPLCONFIGDIR'] = temp_dir.name

shutting_down = False

BUTTON_GPIO_1 = 5
BUTTON_GPIO_2 = 6
BUTTON_GPIO_3 = 13
BUTTON_GPIO_4 = 19


def internet():
    conn = httplib.HTTPConnection("www.google.com", timeout=10)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except Exception as ex:
        logging.warning("No internet")
        logging.warning(ex)
        conn.close()
        return False


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def checkInternetSocket(host="8.8.8.8", port=53, timeout=10):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError as ex:
        print(ex)
        return False


def get_display_size(epd_type):
    epd, mirror, width_first, Use4Gray, Init4Gray, FullUpdate = get_epd(epd_type)
    if width_first:
        return epd.width, epd.height, mirror
    else:
        return epd.height, epd.width, mirror


def draw_image(epd_type, image=None):
    #   A visual cue that the wheels have fallen off
    epd, mirror, width_first, Use4Gray, Init4Gray, FullUpdate = get_epd(epd_type)
    GPIO.setmode(GPIO.BCM)
    if Init4Gray:
        epd.Init_4Gray()
    elif Use4Gray:
        epd.init(0)
    elif FullUpdate:
        epd.init(epd.FULL_UPDATE)
    else:
        epd.init()
    if image is None:
        image = Image.new('L', (epd.height, epd.width), 255)
    logging.info("draw")
    if Use4Gray:
        epd.display_4Gray(epd.getbuffer_4Gray(image))
    else:
        epd.display(epd.getbuffer(image))

    epd.sleep()
    setup_GPIO()


def showmessage(epd_type, ticker, message, mirror, inverted):
    ticker.drawer.inverted = inverted
    ticker.build_message(message, mirror=mirror)
    draw_image(epd_type, ticker.get_image())
    return time.time()


def signal_hook(*args):
    if shutdown_hook():
        logging.info("calling exit 0")
        GPIO.cleanup()
        sys.exit(0)


def shutdown_hook():
    global shutting_down
    if shutting_down:
        return False
    shutting_down = True
    logging.info("...finally going down")
    return True


def init_logging(warnlevel=logging.WARNING):
    logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(warnlevel)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def setup_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def main(config, config_file):

    global epd_type
    epd_type = config.main.epd_type

    w, h, mirror = get_display_size(epd_type)
    if config.main.orientation == 90:
        ticker = Ticker(config, h, w)
    elif config.main.orientation == 270:
        ticker = Ticker(config, h, w)
    else:
        ticker = Ticker(config, w, h)

    height = ticker.mempool.getData()['height']
    # lifetime of 2.7 panel is 5 years and 1000000 refresh
    if config.main.show_block_height:
        # 5*365*(24*60/3.6 + 144) / 1000000
        # Update every 3.6 min + 144 block updates per day
        updatefrequency = 216
    else:
        # 5*365*(24*60/3.0) / 1000000
        # Update every 2.8 min
        updatefrequency = 168
    ticker.set_min_refresh_time(updatefrequency - 1)
    updatefrequency_after_newblock = 120
    # mode_list = ["fiat", "height", "satfiat", "usd", "newblock"]

    layout_list = []
    for layout in config.main.layout_list.split(","):
        layout_list.append(layout.replace('"', "").replace(" ", ""))
    last_layout_ind = config.main.start_layout_ind
    layout_shifting = config.main.layout_shifting
    logging.info(
        "Layout: %s - shifting is set to %d"
        % (layout_list[last_layout_ind], int(layout_shifting))
    )
    mode_list = []
    for mode in config.main.mode_list.split(","):
        mode_list.append(mode.replace('"', "").replace(" ", ""))
    last_mode_ind = config.main.start_mode_ind
    mode_shifting = config.main.mode_shifting
    logging.info(
        "Mode: %s - shifting is set to %d"
        % (mode_list[last_mode_ind], int(mode_shifting))
    )
    # days_list = [1, 7, 30]
    days_list = []
    for d in config.main.days_list.split(","):
        days_list.append(int(d.replace('"', '').replace(" ", "")))

    days_ind = config.main.start_days_ind
    days_shifting = config.main.days_shifting
    logging.info(
        "Days: %d - shifting is set to %d" % (days_list[days_ind], int(days_shifting))
    )

    inverted = config.main.inverted

    def fullupdate(mode, days, layout, inverted, refresh=True):
        try:
            ticker.setDaysAgo(days)
            if refresh:
                ticker.refresh()
            ticker.drawer.inverted = inverted
            ticker.build(mode=mode, layout=layout, mirror=mirror)
            draw_image(epd_type, ticker.get_image())
            lastgrab = time.time()
        except Exception as e:
            logging.warning(e)
            showmessage(epd_type, ticker, e, mirror, inverted)
            time.sleep(10)
            lastgrab = lastcoinfetch
        return lastgrab

    global shutting_down
    setup_GPIO()
    atexit.register(shutdown_hook)
    signal.signal(signal.SIGTERM, signal_hook)

    if True:
        logging.info(
            "BTC ticker %s: set display size to %d x %d"
            % (epd_type, ticker.width, ticker.height)
        )
        signal.signal(signal.SIGINT, signal_handler)

        #       Note that there has been no data pull yet
        datapulled = False
        newblock_displayed = False
        #       Time of start
        lastcoinfetch = time.time()
        lastheightfetch = time.time()

        notifier = sdnotify.SystemdNotifier()
        notifier.notify("READY=1")
        offline_counter = 0
        while True:

            if shutting_down:
                logging.info("Ticker is shutting down.....")
                showmessage(
                    epd_type, ticker, "Ticker is shutting down...", mirror, inverted
                )
                break
            display_update = False
            notifier.notify("WATCHDOG=1")

            if GPIO.input(BUTTON_GPIO_1) == GPIO.LOW:
                logging.info('Key1 after %.2f s' % (time.time() - lastcoinfetch))
                last_mode_ind += 1
                if last_mode_ind >= len(mode_list):
                    last_mode_ind = 0
                display_update = True
            elif GPIO.input(BUTTON_GPIO_2) == GPIO.LOW:
                logging.info('Key2 after %.2f s' % (time.time() - lastcoinfetch))
                days_ind += 1
                if days_ind >= len(days_list):
                    days_ind = 0
                display_update = True
            elif GPIO.input(BUTTON_GPIO_3) == GPIO.LOW:
                logging.info('Key3 after %.2f s' % (time.time() - lastcoinfetch))
                last_layout_ind += 1
                if last_layout_ind >= len(layout_list):
                    last_layout_ind = 0
                display_update = True
            elif GPIO.input(BUTTON_GPIO_4) == GPIO.LOW:
                logging.info('Key4 after %.2f s' % (time.time() - lastcoinfetch))
                inverted = not inverted
                display_update = True
            if (time.time() - lastheightfetch > 30) and config.main.show_block_height:
                try:
                    new_height = ticker.mempool.getData()['height']
                except Exception as e:
                    logging.warning(e)
                if new_height > height and not display_update:
                    logging.info(
                        "Update newblock after %.2f s" % (time.time() - lastcoinfetch)
                    )
                    lastcoinfetch = fullupdate(
                        "newblock",
                        days_list[days_ind],
                        layout_list[last_layout_ind],
                        inverted,
                    )
                    newblock_displayed = True
                height = new_height
                lastheightfetch = time.time()

            if mode_list[last_mode_ind] == "newblock" and datapulled:
                time.sleep(10)
            elif (
                (time.time() - lastcoinfetch > updatefrequency) or (datapulled is False)
            ) and not checkInternetSocket():
                offline_counter += 1
                if offline_counter > 360:
                    local_ip = get_ip()
                    showmessage(
                        epd_type,
                        ticker,
                        "Internet is not available!\nWill retry in 3 minutes.\n"
                        "Check your wpa_supplicant.conf\nIp:%s" % str(local_ip),
                        mirror,
                        inverted,
                    )
                    time.sleep(180)
                    offline_counter = 0
                else:
                    display_update = False
                    time.sleep(10)
            elif display_update:
                fullupdate(
                    mode_list[last_mode_ind],
                    days_list[days_ind],
                    layout_list[last_layout_ind],
                    inverted,
                    refresh=False,
                )
                offline_counter = 0
            elif (time.time() - lastcoinfetch > updatefrequency) or (
                datapulled is False
            ):
                logging.info(
                    "Update ticker after %.2f s" % (time.time() - lastcoinfetch)
                )
                offline_counter = 0
                lastcoinfetch = fullupdate(
                    mode_list[last_mode_ind],
                    days_list[days_ind],
                    layout_list[last_layout_ind],
                    inverted,
                )
                datapulled = True
                if days_shifting:
                    days_ind += 1
                    if days_ind >= len(days_list):
                        days_ind = 0
                if mode_shifting:
                    last_mode_ind += 1
                    if last_mode_ind >= len(mode_list):
                        last_mode_ind = 0
                if layout_shifting:
                    last_layout_ind += 1
                    if last_layout_ind >= len(layout_list):
                        last_layout_ind = 0
            elif newblock_displayed and (
                time.time() - lastcoinfetch > updatefrequency_after_newblock
            ):
                logging.info(
                    "Update from newblock display after %.2f s"
                    % (time.time() - lastcoinfetch)
                )
                offline_counter = 0
                lastcoinfetch = fullupdate(
                    mode_list[last_mode_ind],
                    days_list[days_ind],
                    layout_list[last_layout_ind],
                    inverted,
                )
                datapulled = True
                newblock_displayed = False
            else:
                time.sleep(0.05)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.ini")
    args = parser.parse_args()

    config = Config(path=args.config)
    init_logging(config.main.loglevel)
    try:
        main(config, args.config)
    except Exception as e:
        logging.exception(e)
        raise

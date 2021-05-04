#!/usr/bin/python3
from btcticker.ticker import Ticker
import os
import sys
import math
import socket
import logging
import logging.handlers
import signal
import atexit
import sdnotify
import RPi.GPIO as GPIO
from waveshare_epd import epd2in7
import time
from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw
shutting_down = False
picdir = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources'), 'images')

def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logging.info("No internet")
        return False


def draw_shutdown():
#   A visual cue that the wheels have fallen off
    GPIO.setmode(GPIO.BCM)
    shutdown_icon = Image.open(os.path.join(picdir,'shutdown.bmp'))
    epd = epd2in7.EPD()
    epd.Init_4Gray()
    image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
    image.paste(shutdown_icon, (0,0))
    image = ImageOps.mirror(image)
    epd.display_4Gray(epd.getbuffer_4Gray(image))
    epd.sleep()
    epd2in7.epdconfig.module_exit()


def draw_image(image):
#   A visual cue that the wheels have fallen off
    GPIO.setmode(GPIO.BCM)
    epd = epd2in7.EPD()
    epd.Init_4Gray()
    epd.display_4Gray(epd.getbuffer_4Gray(image))
    epd.sleep()
    epd2in7.epdconfig.module_exit()
    
    

def signal_hook(*args):
    if shutdown_hook():
        logging.info("calling exit 0")
        sys.exit(0)


def shutdown_hook():
    global shutting_down
    if shutting_down:
        return False
    shutting_down = True
    draw_shutdown()
    logging.info("...finally going down")
    return True


def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)


def main():
    ticker = Ticker()
    height = ticker.mempool.getBlockHeight()
    updatefrequency = 300
    mode_list = ["fiat", "height", "satfiat", "usd", "newblock"]
    days_list = [1, 7, 30]
    last_mode_ind = 0
    days_ind = 0
    def fullupdate(mode, days):
        try:
            ticker.sparklinedays = days
            ticker.update(mode=mode)
            draw_image(ticker.image)
            lastgrab=time.time()
        except:
            time.sleep(10)
            lastgrab=lastcoinfetch
        return lastgrab


    global shutting_down

    atexit.register(shutdown_hook)
    signal.signal(signal.SIGTERM, signal_hook)

    if True:
        logging.info("epd2in7 BTC ticker")

        GPIO.setmode(GPIO.BCM)
        key1 = 5
        key2 = 6
        key3 = 13
        key4 = 19

        GPIO.setup(key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(key2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(key3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(key4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#       Note that there has been no data pull yet
        datapulled=False
        newblock_displayed = False
#       Time of start
        lastcoinfetch = time.time()
        lastheightfetch = time.time()

        notifier = sdnotify.SystemdNotifier()
        notifier.notify("READY=1")
     
        while True:
            if shutting_down:
                logging.info("App is shutting down.....")
                break
            display_update = False
            GPIO.setmode(GPIO.BCM)
            key1 = 5
            key2 = 6
            key3 = 13
            key4 = 19

            GPIO.setup(key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(key2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(key3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(key4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


            key1state = GPIO.input(key1)
            key2state = GPIO.input(key2)
            key3state = GPIO.input(key3)
            key4state = GPIO.input(key4)

            notifier.notify("WATCHDOG=1")
            if internet():
                if key1state == False:
                    logging.info('Key1')
                    last_mode_ind += 1
                    if last_mode_ind >= len(mode_list):
                        last_mode_ind = 0
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind])
                    display_update = True                    
                elif key2state == False:
                    logging.info('Key2')
                    days_ind += 1
                    if days_ind >= len(days_list):
                        days_ind = len(days_list) - 1
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind])
                    display_update = True                    
                elif key3state == False:
                    logging.info('Key3')
                    lastcoinfetch = fullupdate("newblock", days_list[days_ind])
                    display_update = True
                    newblock_displayed = True
                elif key4state == False:
                    logging.info('Key4')
                    lastcoinfetch = fullupdate(mode_list[last_mode_ind], days_list[days_ind])
                    display_update = True
                if (time.time() - lastheightfetch > 10):
                    new_height = ticker.mempool.getBlockHeight()
                    if new_height > height and not display_update:
                        lastcoinfetch = fullupdate("newblock", days_list[days_ind])
                        newblock_displayed = True
                    height = new_height
                    lastheightfetch = time.time()
                    
                if (time.time() - lastcoinfetch > updatefrequency) or (datapulled==False):
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind])
                    datapulled = True
                elif newblock_displayed and (time.time() - lastcoinfetch > 150):
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind])
                    datapulled = True                    
                else:
                    time.sleep(0.5)


if __name__ == '__main__':
    init_logging()
    try:
        main()
    except Exception as e:
        logging.exception(e)
        raise
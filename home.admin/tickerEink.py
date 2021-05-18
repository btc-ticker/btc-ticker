#!/usr/bin/python3
from btcticker.ticker import Ticker
from btcticker.config import Config
import os
import sys
import math
import socket
import logging
import logging.handlers
import argparse
import signal
import atexit
import sdnotify
import RPi.GPIO as GPIO
from waveshare_epd import epd2in7, epd7in5_HD
import time
from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw
shutting_down = False
picdir = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets'), 'images')

BUTTON_GPIO_1 = 5
BUTTON_GPIO_2 = 6
BUTTON_GPIO_3 = 13
BUTTON_GPIO_4 = 19

def internet(host="8.8.8.8", port=53, timeout=6):
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
        logging.warning("No internet")
        logging.warning(ex)
        return False

def get_display_size(epd_type):
    if epd_type == "2in7_gray4":
        epd = epd2in7.EPD()
        mirror = True
        return epd.width, epd.height, mirror
    elif epd_type == "2in7":
        epd = epd2in7.EPD()
        mirror = False
        return epd.width, epd.height, mirror    
    else:
        epd = epd7in5_HD.EPD()
        mirror = False
        return epd.height, epd.width, mirror
    

def draw_shutdown():
    global epd_type
#   A visual cue that the wheels have fallen off
    cleanup_GPIO()
    GPIO.setmode(GPIO.BCM)
    shutdown_icon = Image.open(os.path.join(picdir,'shutdown.bmp'))
    if epd_type == "2in7_4gray":
        epd = epd2in7.EPD()
        epd.Init_4Gray()
        image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
        # image.paste(shutdown_icon, (0,0))
        image = ImageOps.mirror(image)
        epd.display_4Gray(epd.getbuffer_4Gray(image))
    elif epd_type == "2in7":
        epd = epd2in7.EPD()
        epd.init()
        image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
        # image.paste(shutdown_icon, (0,0))
        epd.display(epd.getbuffer(image))          
    else:
        epd = epd7in5_HD.EPD()
        epd.init()
        image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
        # image.paste(shutdown_icon, (0,0))
        epd.display(epd.getbuffer(image))        

    epd.sleep()
    GPIO.setmode(GPIO.BCM)
    epd2in7.epdconfig.module_exit()


def draw_image(epd_type, image=None):
#   A visual cue that the wheels have fallen off
    cleanup_GPIO()
    GPIO.setmode(GPIO.BCM)
    if epd_type == "2in7_4gray":
        epd = epd2in7.EPD()
        epd.Init_4Gray()
        if image is None:
            image = Image.new('L', (epd.height, epd.width), 255)
        logging.info("draw")
        epd.display_4Gray(epd.getbuffer_4Gray(image))
    elif epd_type == "2in7":
        epd = epd2in7.EPD()
        epd.init()
        if image is None:
            image = Image.new('L', (epd.height, epd.width), 255)
        logging.info("draw")
        epd.display(epd.getbuffer(image))          
    else:
        epd = epd7in5_HD.EPD()    
        epd.init()
        if image is None:
            image = Image.new('L', (epd.height, epd.width), 255)
        logging.info("draw")
        epd.display(epd.getbuffer(image))
    epd.sleep()
    setup_GPIO(False)
    

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


def init_logging(warnlevel=logging.WARNING):
    logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(warnlevel)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

def cleanup_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.remove_event_detect(BUTTON_GPIO_1)
    GPIO.remove_event_detect(BUTTON_GPIO_2)
    GPIO.remove_event_detect(BUTTON_GPIO_3)
    GPIO.remove_event_detect(BUTTON_GPIO_4)
    GPIO.cleanup()    

def setup_GPIO(cleanup=True):
    if cleanup:
        cleanup_GPIO()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_GPIO_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    try:
        
        GPIO.add_event_detect(BUTTON_GPIO_1, GPIO.FALLING, 
                              callback=button_pressed_callback1, bouncetime=100)
        GPIO.add_event_detect(BUTTON_GPIO_2, GPIO.FALLING, 
                              callback=button_pressed_callback2, bouncetime=100)
        GPIO.add_event_detect(BUTTON_GPIO_3, GPIO.FALLING, 
                              callback=button_pressed_callback3, bouncetime=100)
        GPIO.add_event_detect(BUTTON_GPIO_4, GPIO.FALLING, 
                              callback=button_pressed_callback4, bouncetime=100)
    except Exception as e:
        logging.warning(e)
        

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def button_pressed_callback1(channel):
    global key1state
    key1state = False

def button_pressed_callback2(channel):
    global key2state
    key2state = False

def button_pressed_callback3(channel):
    global key3state
    key3state = False

def button_pressed_callback4(channel):
    global key4state
    key4state = False

def clear_state():
    global key1state
    global key2state
    global key3state
    global key4state
    key1state = True
    key2state = True
    key3state = True
    key4state = True


def main(config, config_file):
    
    global epd_type
    epd_type = config.main.epd_type

    w, h, mirror = get_display_size(epd_type)
    
    ticker = Ticker(config, w, h)

    height = ticker.mempool.getBlockHeight()
    # lifetime of 2.7 panel is 5 years and 1000000 refresh
    if config.main.show_block_height:
        # 5*365*(24*60/3.6 + 144) / 1000000
        # Update every 3.6 min + 144 block updates per day
        updatefrequency = 216
    else:
        # 5*365*(24*60/3.0) / 1000000
        # Update every 2.8 min
        updatefrequency = 168       
    updatefrequency_after_newblock = 120
    # mode_list = ["fiat", "height", "satfiat", "usd", "newblock"]
    
    layout_list = []
    for l in config.main.layout_list.split(","):
        layout_list.append(l.replace('"', "").replace(" ", ""))
    last_layout_ind = config.main.start_layout_ind    
    
    mode_list = []
    for l in config.main.mode_list.split(","):
        mode_list.append(l.replace('"', "").replace(" ", ""))
    # days_list = [1, 7, 30]
    days_list = []
    for d in config.main.days_list.split(","):
        days_list.append(int(d.replace('"', '').replace(" ", "")))    
    last_mode_ind = config.main.start_mode_ind
    days_ind = config.main.start_days_ind
    def fullupdate(mode, days, layout, refresh=True):
        try:
            ticker.setDaysAgo(days)
            if refresh:
                ticker.refresh()
            ticker.build(mode=mode, layout=layout, mirror=mirror)
            draw_image(epd_type, ticker.image)
            lastgrab=time.time()
        except Exception as e:
            logging.warning(e)
            time.sleep(10)
            lastgrab=lastcoinfetch
        return lastgrab


    global shutting_down
    global key1state
    global key2state
    global key3state
    global key4state    

    clear_state()

    atexit.register(shutdown_hook)
    signal.signal(signal.SIGTERM, signal_hook)

    if True:
        logging.info("BTC ticker %s: set display size to %d x %d" % (epd_type, ticker.width, ticker.height))

        setup_GPIO(False)
        signal.signal(signal.SIGINT, signal_handler)
   

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

            notifier.notify("WATCHDOG=1")
            if internet():
                if key1state == False:
                    logging.info('Key1 after %.2f s' % (time.time() - lastcoinfetch))
                    last_mode_ind += 1
                    if last_mode_ind >= len(mode_list):
                        last_mode_ind = 0
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind], layout_list[last_layout_ind], refresh=False)
                    display_update = True     
                    clear_state()
                    setup_GPIO()
                elif key2state == False:
                    logging.info('Key2 after %.2f s' % (time.time() - lastcoinfetch))
                    days_ind += 1
                    if days_ind >= len(days_list):
                        days_ind = 0
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind], layout_list[last_layout_ind], refresh=False)
                    display_update = True  
                    clear_state()
                    setup_GPIO()
                elif key3state == False:
                    logging.info('Key3 after %.2f s' % (time.time() - lastcoinfetch))
                    last_layout_ind += 1
                    if last_layout_ind >= len(layout_list):
                        last_layout_ind = 0
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind], layout_list[last_layout_ind], refresh=False)
                    display_update = True  
                    clear_state()
                    setup_GPIO()
                elif key4state == False:
                    logging.info('Key4 after %.2f s' % (time.time() - lastcoinfetch))
                    lastcoinfetch = fullupdate("newblock", days_list[days_ind], layout_list[last_layout_ind], refresh=False)
                    display_update = True
                    newblock_displayed = True
                    clear_state()
                    setup_GPIO()
                if (time.time() - lastheightfetch > 30) and config.main.show_block_height:
                    try:
                        new_height = ticker.mempool.getBlockHeight()
                    except Exception as e:
                        logging.warning(e)
                    if new_height > height and not display_update:
                        logging.info("Update newblock after %.2f s" % (time.time() - lastcoinfetch))
                        lastcoinfetch = fullupdate("newblock", days_list[days_ind], layout_list[last_layout_ind])
                        newblock_displayed = True
                        setup_GPIO()
                    height = new_height
                    lastheightfetch = time.time()
                
                if mode_list[last_mode_ind] == "newblock" and datapulled:
                    time.sleep(10)
                elif (time.time() - lastcoinfetch > updatefrequency) or (datapulled==False):
                    logging.info("Update ticker after %.2f s" % (time.time() - lastcoinfetch))
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind], layout_list[last_layout_ind])
                    datapulled = True
                    setup_GPIO()
                elif newblock_displayed and (time.time() - lastcoinfetch > updatefrequency_after_newblock):
                    logging.info("Update from newblock display after %.2f s" % (time.time() - lastcoinfetch))
                    lastcoinfetch=fullupdate(mode_list[last_mode_ind], days_list[days_ind], layout_list[last_layout_ind])
                    datapulled = True
                    newblock_displayed = False
                    setup_GPIO()
                else:
                    time.sleep(1)


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
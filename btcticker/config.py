import os
from configparser import ConfigParser
from pydantic import BaseModel, validator, HttpUrl



class ConfigurationException(ValueError):
    """Configuration Exception"""


class MainConfig(BaseModel):
    fiat: str = 'eur'
    mode_list: str ='fiat,height,satfiat,moscowtime,usd'
    start_mode_ind: int = 0
    mode_shifting: bool = False
    days_list: str = '1,3,7'
    start_days_ind: int = 0
    days_shifting: bool = False
    layout_list: str = 'all,fiat,fiatheight,big_one_row,one_number,mempool,ohlc'
    start_layout_ind: int = 0
    layout_shifting : bool = False
    loglevel: str = 'WARNING'
    orientation: int = 0
    inverted: bool = False
    show_block_height: bool = False
    update_on_new_block: bool = True
    mempool_api_url: str = 'https://mempool.space/api/'
    epd_type: str = '2in7_4gray'
    show_best_fees: bool = True
    show_block_time: bool = True

class FontsConfig(BaseModel):

    font_buttom: str = 'googlefonts/Audiowide-Regular.ttf'
    font_console: str = 'googlefonts/ZenDots-Regular.ttf'
    font_big: str = 'googlefonts/BigShouldersDisplay-SemiBold.ttf'
    font_side: str = 'googlefonts/Roboto-Medium.ttf'
    font_side_size: int = 20
    font_top: str = 'PixelSplitter-Bold.ttf'
    font_top_size: int = 18
    font_fee: str = 'googlefonts/Audiowide-Regular.ttf'
    font_fee_size :int = 14


class Config:
    def __init__(self, path='config.ini'):
        self.__config = ConfigParser()
        self.__config.read(path)
        self.main = MainConfig(**self.__config['Main'])
        self.fonts = FontsConfig(**self.__config['Fonts'])

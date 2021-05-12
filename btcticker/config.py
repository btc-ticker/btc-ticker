import os
from configparser import ConfigParser
from pydantic import BaseModel, validator, HttpUrl



class ConfigurationException(ValueError):
    """Configuration Exception"""


class MainConfig(BaseModel):
    fiat: str = 'eur'
    mode_list: str ='fiat,height,satfiat,usd'
    start_mode_ind: int = 0
    days_list: str = '1,7,30'
    start_days_ind: int = 0
    layout_list: str = 'all,fiat,fiatheight,big'
    start_layout_ind: int = 0
    loglevel: str = "WARNING"
    orientation: int = 90
    inverted: bool = False
    show_block_height: bool = True
    mempool_api_url: str = "https://mempool.space/api/"
    epd_type: str = "2in7"

class FontsConfig(BaseModel):

    font_buttom: str = 'googlefonts/Roboto-Medium.ttf'
    font_console: str = 'googlefonts/ZenDots-Regular.ttf'
    font_side: str = 'googlefonts/Roboto-Medium.ttf'
    font_side_size: int = 20
    font_top: str = 'PixelSplitter-Bold.ttf'
    font_top_size: int = 18
    font_fee: str = 'googlefonts/RobotoMono-Medium.ttf'
    font_fee_size :int = 15


class Config:
    def __init__(self, path='config.ini'):
        self.__config = ConfigParser()
        self.__config.read(path)
        self.main = MainConfig(**self.__config['Main'])
        self.fonts = FontsConfig(**self.__config['Fonts'])

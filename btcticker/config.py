import os
from configparser import ConfigParser
from pydantic import BaseModel, validator, HttpUrl



class ConfigurationException(ValueError):
    """Configuration Exception"""


class MainConfig(BaseModel):
    fiat: str = "eur"
    show_usd: bool = True
    loglevel: str = "WARNING"
    display_width_pixels: int = 264
    display_height_pixels: int = 176
    orientation: int = 90
    inverted: bool = False
    show_block_height: bool = True
    big_number: bool = False

class FontsConfig(BaseModel):
    
    fonthiddenprice: str = 'googlefonts/Roboto-Medium.ttf'
    fonthiddenpricesize: int = 30
    font: str = 'googlefonts/Roboto-Medium.ttf'
    font_size: int = 40
    font_horizontalblock: str = 'googlefonts/Roboto-Medium.ttf'
    font_horizontalbig: str = 'googlefonts/Roboto-Medium.ttf'
    font_price: str = 'googlefonts/Roboto-Medium.ttf'
    font_price_size: int = 20
    font_height: str = 'PixelSplitter-Bold.ttf'
    font_height_size: int = 18
    font_date: str = 'googlefonts/RobotoMono-Medium.ttf'
    font_date_size :int = 15


class Config:
    def __init__(self, path='config.ini'):
        self.__config = ConfigParser()
        self.__config.read(path)
        self.main = MainConfig(**self.__config['Main'])
        self.fonts = FontsConfig(**self.__config['Fonts'])

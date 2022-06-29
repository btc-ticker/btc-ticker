import codecs
import io
import os
import sys

from setuptools import setup

VERSION = '0.5.0'

tests_require = ['pytest']

requires = [
    "requests",
    "babel",
    "pycoingecko",
    "blockchain",
    "pymempool",
    "Pillow",
    "matplotlib",
    "numpy",
    "pydantic",
    "mplfinance",
    "pandas"
]

if __name__ == '__main__':
    setup(
        name='btc-ticker',
        version=VERSION,
        description='BTC ticker',
        url='http://www.github.com/btc-ticker/btc-ticker',
        keywords=['btc', 'ticker'],
        packages=[
            "btcticker",
            "btcticker.fonts",
            "btcticker.fonts.googlefonts"
        ],
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: Financial and Insurance Industry',
            'Topic :: Office/Business :: Financial',
        ],
        install_requires=requires,
        package_data={'btcticker.fonts': ['*.ttf'], 'btcticker.fonts.googlefonts': ['*.ttf', '*.txt'], },
        setup_requires=['pytest-runner'],
        tests_require=tests_require,
        include_package_data=True,
    )
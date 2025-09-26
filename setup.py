import os
from setuptools import setup

__author__ = "Jo0x01"
__pkg_name__ = "Anime3rbDL"
__version__ = "1.0.8"
__desc__ = "Anime3rbDL is a robust, feature-rich command-line application designed for anime enthusiasts. It enables seamless searching, browsing, and downloading of high-quality anime episodes directly from the Anime3rb platform. Featuring advanced logging capabilities, customizable color output, multi-resolution support, batch downloading, and comprehensive CLI options, it provides a powerful yet user-friendly experience for managing anime collections efficiently."

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=__pkg_name__,
    version=__version__,
    packages=[__pkg_name__],
    license='MIT',
    description=__desc__,
    author=__author__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/Jo0X01/Anime3rbDL",
    py_modules=["Anime3rbDL"],
    install_requires=[
        "beautifulsoup4==4.13.5",
        "cloudscraper==1.2.71",
        "fake-useragent>=0.1.11",
        "pydoll-python==2.8.0",
        "psutil>=7.1.0"
    ],
    entry_points={
        "console_scripts": [
            "A3rbDL=Anime3rbDL.__main__:main",
            "An3rbDL=Anime3rbDL.__main__:main",
            "Anime3rbDL=Anime3rbDL.__main__:main",
        ]
    },
    keywords="anime, downloader, cli, Anime3rb, video, download, logging, scraper, automation, command-line, python, episodes, series, entertainment, media, streaming, batch-download, high-quality, fast, reliable, color-output, multi-resolution, anime-collection, media-downloader, web-scraper, terminal-tool, open-source",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.8",
)

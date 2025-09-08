import os
from setuptools import setup, find_packages

__author__ = "Jo0x01"
__pkg_name__ = "Anime3rbDL"
__version__ = "1.0.1"
__desc__ = """A simple and fast command-line tool to **search, retrieve, and download anime episodes** from **[Anime3rb](https://anime3rb.com)**."""

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
    url="https://github.com/jo0x01/Anime3rbDL",
    py_modules=["Anime3rbDL"],
    install_requires=[
        "beautifulsoup4==4.13.5",
        "cloudscraper==1.2.71"
    ],
    entry_points={
        "console_scripts": [
            "An3rbDL=Anime3rbDL:main",
            "Anime3rbDL=Anime3rbDL:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.2",
)

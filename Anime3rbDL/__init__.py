from .parser import Parser,Client,Cache,Config
from .cli import CLI
from .downloader import Downloader
import os

class Anime3rbDL(CLI,Config,Cache):
    def __init__(self):
        super().__init__()

    def search(self,url:str):
        if Parser.parse_url(url):
            return Parser.parse_title_page()
        _eps = Parser.parse_search_page()
        if len(_eps) == 1:
            Parser.parse_url(_eps[0]["link"])
            return Parser.parse_title_page()

    def get_info(self,skip_parts="all"):
        Parser.parse_skip_parts(skip_parts)
        return Parser.parse_episodes_links()

    def show_download_info(self,res="low"):
        if not res:
            res = "480p"
        for ep in Cache.EpisodesDownloadData:
            CLI.show_download_data(ep[res])

    def download(self,path=".",res="480p"):
        if not res:
            res = "480p"
        output_dir = f"{path}/{Cache.ANIME_TITLE}/"
        os.makedirs(output_dir,mode=0o777,exist_ok=True)
        for episode in Cache.EpisodesDownloadData:
            _data = episode[res]
            Downloader.download(Client.scraper,_data["link"],_data["filename"],output_dir)
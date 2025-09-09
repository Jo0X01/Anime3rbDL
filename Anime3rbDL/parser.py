from Anime3rbDL.config import APIConfig, Cache,Config
import re
from bs4 import BeautifulSoup as bs4
import json
from Anime3rbDL.client import Client

class Parser:
    @staticmethod
    def format_bytes(size):
        if size==0:
            return "0 B"
        uints = ["B","KB","MB","GB","TB","PB"]
        index = 0
        size = float(size)
        while size >=1024 and index < len(uints) - 1:
            size /= 1024
            index +=1
        return f"{size:.2f}{uints[index]}"
    @staticmethod
    def parse_filename(filename: str, replacement: str = "_") -> str:
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, replacement, filename)
        filename = filename.rstrip(' .')
        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))
        }
        if filename.upper().split('.')[0] in reserved_names:
            filename = f"{replacement}{filename}"
        return filename
    
    @staticmethod
    def parse_url(_url:str):
        _url = str(_url)
        if _url.endswith("/"):
            _url = _url[:-1]
        if _url.startswith("https"):
            _url = _url.split("/")[-1]
            Cache.USER_INPUT_URL = _url
            Cache.ANIME_URL = Config.TitleURL + _url
            Cache.ANIME_TITLE = _url.replace("-"," ")
            return True
        Cache.USER_INPUT_URL = _url.strip()
        return False

    @staticmethod
    def parse_skip_parts(_input:str) -> list[int]:
        _input = str(_input).lower().replace(" ",",").strip()
        if not _input or _input == "all":
            Config.SkipParts = []
            return
        skip_episodes = []
        for _part in _input.split(","):
            if "-" in _part:
                start,end = _part.split("-")
                start,end = int(start)-1,int(end)-1
                while not start == end + 1:
                    skip_episodes.append(start)
                    start += 1
            else:
                skip_episodes.append(int(_part)-1)
        Config.SkipParts = skip_episodes

    @staticmethod
    def parse_qualities_data(_html):
        _data = {}
        _html = bs4(_html,"html.parser")
        title = _html.find("title").string
        qualities = _html.find_all("div",{"class":"flex flex-col flex-grow sm:max-w-[300px] rounded-lg overflow-hidden bg-gray-50 dark:bg-dark-700"})
        for q in qualities:
            link = q.find("a").attrs["href"]
            label = q.find("label").string
            size = q.find("a").string
            fsize = re.search(r"(\d+\.\d+)",size).group(1)
            size = int(round(float(fsize) * 1024 * 1024))
            fsize = Parser.format_bytes(size)
            res = re.search(r"\[(\d+p)\]",label).group(1)

            if res == "1080p":
                Cache.HighTotalSize += size
            elif res == "720p":
                Cache.MidTotalSize += size
            elif res == "480p":
                Cache.LowTotalSize += size
            else:
                Cache.UnknownSize += size

            _data[res] = {
                "link":link,
                "fsize":fsize,
                "size":size,
                "filename":Parser.parse_filename(title)+".mp4"
            }
        return _data

    @staticmethod
    def parse_episodes_links():
        _data = []
        _index = 0
        for url in Cache.ANIME_INFO_DATA['ep-urls']:
            if Config.SkipParts==[] or _index in Config.SkipParts:
                _data.append(Parser.parse_qualities_data(Client.get_req(url)))
            _index+=1
        Cache.EpisodesDownloadData = _data
        return Cache.EpisodesDownloadData

    @staticmethod
    def parse_title_page(max_retries: int = 2):
        last_error = None
        data = None
        html = None

        for attempt in range(max_retries):
            html = Client.get_req(Cache.ANIME_URL)
            if not html:
                last_error = f"Empty response for URL: {Cache.ANIME_URL}"
                continue

            soup = bs4(html, "html.parser")
            script_tag = soup.find("script", {"type": "application/ld+json"})
            if not script_tag or not script_tag.string:
                last_error = "Missing or empty JSON-LD script tag."
                continue

            try:
                data = json.loads(script_tag.string)
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                continue

            _type = data.get("@type")
            if _type == "Episode":
                data["ep-urls"] = [data.get("url")]
                break

            elif _type == "Movie":
                # Convert titles URL to episode URL for movies
                Cache.ANIME_URL = f"{Cache.ANIME_URL.replace('titles', 'episode').rstrip('/')}/1"
                continue

            elif _type == "TVSeries":
                episodes = data.get("episode")
                if not episodes:
                    last_error = "No episodes found for TVSeries."
                    continue
                data["ep-urls"] = [ep.get("url") for ep in episodes if "url" in ep]
                break

            else:
                last_error = f"Unknown content type: {_type}"
                continue
        else:
            raise RuntimeError(f"Failed to parse anime info from: {Cache.ANIME_URL} | Reason: {last_error}")

        Cache.ANIME_INFO_HTML = html
        Cache.ANIME_INFO_DATA = data
        return data




    @staticmethod
    def parse_search_page():
        _html = bs4(Client.get_req(Config.WebsiteURL),"html.parser")
        _snapshot = _html.find("form",{"action":Config.SearchURL}).attrs["wire:snapshot"]
        APIConfig.SearchPayload["_token"] = _html.find("meta",{"name":"csrf-token"}).attrs["content"] 
        APIConfig.SearchPayload["components"][0]["snapshot"] = json.dumps(json.loads(_snapshot))
        APIConfig.SearchPayload["components"][0]["updates"]["query"] = Cache.USER_INPUT_URL
        _response = Client.post_req(
            Config.SearchAPI,
            payload=APIConfig.SearchPayload,
            headers=APIConfig.SearchHeaders,
        )
        soup = bs4(_response["components"][0]["effects"]["html"], "html.parser")
        results = []
        for a in soup.find_all("a", href=re.compile(r"^https://anime3rb\.com/titles/.*")):
            details = a.find("div",{"class":"details"})
            title = details.find("h4",{"class":"text-lg"}).get_text(strip=True)
            description = details.find("h5",{"class":"text-sm"}).get_text(strip=True)
            link = a["href"]
            image = a.select_one("img")["src"]
            rate,count,year = details.select(".badge")
            try: rate = re.search(r"([0-9\.]+)",rate.get_text(strip=True)).group(1)
            except: rate = "0.0"
            try: count = re.search(r"([0-9\.]+)",count.get_text(strip=True)).group(1)
            except: count = "UnKnown"
            try: year = re.search(r"([0-9\.]+)",year.get_text(strip=True)).group(1)
            except: year = "UnKnown"
            results.append({
                "title": Parser.parse_filename(title),
                "link": link,
                "image": image,
                "desc": description,
                "rate":rate,
                "count":count,
                "year":year
            })
        Cache.SearchResult = results
        return Cache.SearchResult

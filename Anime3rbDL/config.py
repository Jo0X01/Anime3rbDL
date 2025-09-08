
class Config:
    Skip = True
    DownloadSkipped = False
    SkipParts = []
    WebsiteURL = "https://anime3rb.com/"
    TitleURL = "https://anime3rb.com/titles/"
    SearchURL = "https://anime3rb.com/search"
    SearchAPI = "https://anime3rb.com/livewire/update"
    DefaultResoultion = {"low":"480p","mid":"720p","high":"1080p"}
    
class APIConfig:
    SearchPayload = {
        "components":[{
            "calls":[],
            "snapshot":None,
            "updates":{"query":None,"deep":True}
          }],
        "_token":None
    }
    SearchHeaders = {
        "content-type":"application/json",
        "referer":Config.TitleURL+"list",
        "origin":Config.WebsiteURL,
        "x-livewire":"",
    }
    
class Cache:
    USER_INPUT_URL:str = None
    ANIME_TITLE:str = None
    ANIME_URL:str = None
    ANIME_INFO_HTML:bytes = None
    ANIME_SEARCH_STR:str = None
    ANIME_SEARCH_HTML:bytes = None
    ANIME_INFO_DATA:dict = None
    ANIME_SEARCH_INFO_DATA:dict = None
    EpisodesDownloadData:list[dict] = []
    HighTotalSize = 0
    MidTotalSize = 0
    LowTotalSize = 0
    UnknownSize = 0
    SearchResult:list[dict] = []

import json
import re
import bs4
from client import Client
from bs4 import BeautifulSoup as bs4

_html = bs4(Client.get_req(Config.WebsiteURL),"html.parser")
_snapshot = _html.find("form",{"action":Config.SearchURL}).attrs["wire:snapshot"]
APIConfig.SearchPayload["_token"] = _html.find("meta",{"name":"csrf-token"}).attrs["content"] 
APIConfig.SearchPayload["components"][0]["snapshot"] = json.dumps(json.loads(_snapshot))
APIConfig.SearchPayload["components"][0]["updates"]["query"] = "k"
_response = Client.post_req(
    Config.SearchAPI,
    payload=APIConfig.SearchPayload,
    headers=APIConfig.SearchHeaders,
)
soup = bs4(_response["components"][0]["effects"]["html"], "html.parser")
# open("se    arch.json","wb").write(json.dumps(_response).encode())
# open("test_search.html","wb").write(soup.__str__().encode())

results = []
for a in soup.find_all("a", href=re.compile(r"^https://anime3rb\.com/titles/.*")):
    details = a.find("div",{"class":"details"})
    title = details.find("h4",{"class":"text-lg"}).get_text(strip=True)
    description = details.find("h5",{"class":"text-sm"}).get_text(strip=True)
    link = a["href"]
    image = a.select_one("img")["src"]
    rate,count,year = details.select(".badge")
    rate = re.search(r"([\d+\.]+)",rate.get_text(strip=True)).group(1)
    count = re.search(r"(\d+)",count.get_text(strip=True)).group(1)
    year = re.search(r"(\d+)",year.get_text(strip=True)).group(1)
    results.append({
        "title": title,
        "link": link,
        "image": image,
        "description": description,
        "rate":rate,
        "count":count,
        "year":year
    })
    
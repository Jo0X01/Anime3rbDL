
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
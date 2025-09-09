from Anime3rbDL.parser import Parser, Cache

class CLI:
    @staticmethod
    def show_anime_info(_info:dict=None):
        if _info == None:
            if Cache.ANIME_INFO_DATA:
                _data = Cache.ANIME_INFO_DATA
        else:
            _data = _info
        print("     .... Anime Info ....")
        print("="*40)
        print("[+] Title: ",Parser.parse_filename(_data["name"]))
        print("[+] Banner URL: ",_data["image"])
        print("[+] All Episodes: ",_data["numberOfEpisodes"])
        print("[+] Publish Date: ",_data["datePublished"])
        print("[+] Type: ",_data["@type"])
        print("[+] Rating: ",_data["aggregateRating"]["ratingValue"])
        print("[+] Rating Count: ",_data["aggregateRating"]["ratingCount"])
        print("[+] Best Rating: ",_data["aggregateRating"]["bestRating"])
        print("[+] Worst Rating: ",_data["aggregateRating"]["worstRating"])
        print("[+] Contributor: ")
        for _d in _data["contributor"]:
            print("    [-] "+_d["name"])
            print("    [-] "+_d["url"])
        print("="*40)

    @staticmethod
    def show_episodes_info():
        print("     .... Anime Episodes Info ....")
        print("="*40)
        print("[+] Total Episodes: ",len(Cache.EpisodesDownloadData))
        print("[+] High [1080p] ≈ ",Parser.format_bytes(Cache.HighTotalSize))
        print("[+] Mid [720p]     ≈ ",Parser.format_bytes(Cache.MidTotalSize))
        print("[+] Low [480p]     ≈ ",Parser.format_bytes(Cache.LowTotalSize))
        print("="*40)

    @staticmethod
    def show_download_data(data):
        print("    ... Download Data ...")
        print("-"*40)
        print("[+] Filename: ")
        print(data["filename"])
        print(f"[+] FileSize: ",data["fsize"])
        print("[+] Direct Download Link: ")
        print(data["link"])
        print("-"*40)

    @staticmethod
    def show_search_data(data:list[dict]=None):
        if data == None:
            if Cache.SearchResult:
                data = Cache.SearchResult
        counter = 1
        print(f"    ... Search Results [{len(data)}] ...")
        print("-"*40)
        for _data in data:
            print(f"[+] Choose Number: [{counter}]")
            print("[+] Title: ",_data["title"])
            # print("[+] Description: ",_data["desc"][:15],"...")
            print("[+] Banner Image: ",_data["image"])
            print("[+] Page Link: ",_data["link"])
            print(f"[+] Episodes: {_data["count"]} , Year: {_data['year']} , Rate: {_data['rate']}")
            print("-"*40)
            counter+=1

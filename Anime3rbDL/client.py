import cloudscraper

class Client:
    scraper = cloudscraper.create_scraper()
    
    @staticmethod
    def create():
        return cloudscraper.create_scraper()

    @staticmethod
    def get_req(url) -> bytes:
        return Client.scraper.get(url,allow_redirects=True).content

    @staticmethod
    def post_req(url,payload:dict,headers:dict={}) -> dict:
        return Client.scraper.post(url,json=payload,headers=headers).json()
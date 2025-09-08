import os
from .parser import Parser

class Downloader:
    @staticmethod
    def download(_scarper,url,filename,output_dir):
        if not filename:
            filename = url.split("/")[-1]
            filename = Parser.parse_filename(filename)
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, filename)
        file_mode = 'ab' if os.path.exists(file_path) else 'wb'
        current_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        headers = {}
        if current_size > 0:
            headers['Range'] = f'bytes={current_size}-'
        response = _scarper.get(url, stream=True, headers=headers)
        if response.status_code == 416:
            print(f"[✅] Already fully downloaded: {file_path}")
            return file_path
        size = int(response.headers["Content-Length"])
        with open(file_path, file_mode) as f:
                for chunk in response.iter_content(chunk_size=8192*8):
                    if chunk:
                        f.write(chunk)
                        current_size+=len(chunk)
                        print(f"\rDownloading : {Parser.format_bytes(current_size)}/{Parser.format_bytes(size)}       ",end="\r")
                print(f"[✅] Downloaded (or resumed): {file_path}")
                return file_path
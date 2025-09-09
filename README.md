<p align="left">
  <a href="https://github.com/Jo0X01/Anime3rbDL">
    <img src="https://raw.githubusercontent.com/Jo0X01/Anime3rbDL/refs/heads/main/Anime3rbDL.ico" alt="Anime3rbDL">
  </a>
</p>
<p align="left">
  <a href="https://pypi.org/project/Anime3rbDL/">
    <img src="https://img.shields.io/badge/-PyPi-blue.svg?logo=pypi&labelColor=555555&style=for-the-badge" alt="PyPi">
  </a>
  <a href="https://github.com/Jo0X01/Anime3rbDL">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License: MIT">
  </a>
</p>


# Anime3rbDL

A simple and fast command-line tool to **search, retrieve, and download anime episodes** from **[Anime3rb](https://anime3rb.com)**.

---

## Features

- Search by name or direct URL
- Show detailed episode information
- Download specific episodes or full series
- Supports resolutions: low (480p), mid (720p), high (1080p)
- Lightweight CLI-based tool

---

## Installation

#### Via Source:

```bash
git clone https://github.com/Jo0X01/Anime3rbDL.git
cd Anime3rbDL
pip install -r requirements.txt
```

#### Via Pypi:

```bash
pip install Anime3rbDL
```
---

## Usage

```bash
Anime3rbDL "Naruto" --res mid --download
```

### Options:
- `SEARCH_OR_URL` → Anime name or link
- `--download-parts 1-5` → Range of episodes
- `--res low|mid|high` → Resolution (default: low/480p)
- `--path ./downloads` → Set download folder
- `--download` → Start download after showing info

---

### Example

```bash
Anime3rbDL "One Piece" --res high --download-parts 1-3 --download
```

---

### Python Code

```python
from Anime3rbDL import Anime3rbDL

anime = Anime3rbDL()
filters = anime.search("anime-url or anime-name")
if isinstance(filters,list):
  # its search system
  anime.search(filters[0]) # or choose ur input

# 1-6: mean 1,2,3,4,5,6 and 8,12
anime.get_info(download_parts="1-6,8,12") # this parts will be downloaded 

resolution = "low" # low/480p , mid/720p , high/108p
anime.download(path=_download_dir,res=resolution)
```

---
## License

MIT © 2025 Mr.Jo0x01

---

## Disclaimer

For **educational use only**. Downloading copyrighted material without permission may be illegal in your country.

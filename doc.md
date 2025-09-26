# 🎌 Anime3rbDL Documentation

## 📖 Overview

Anime3rbDL is a powerful command-line tool and Python library for downloading anime episodes from [Anime3rb](https://anime3rb.com). It features Cloudflare bypass, multi-resolution support, and intelligent download management.

**Key Features:**
- 🔍 Smart search by name or URL
- 📥 Bulk downloads with resume support
- 🎥 Multi-resolution (480p/720p/1080p)
- 🤖 Automated Cloudflare bypass
- 🔐 User authentication
- ⚡ Multi-threaded downloads
- 🌐 Proxy support

## 📦 Installation

Install via PyPI or from source:

```bash
# PyPI (recommended)
pip install Anime3rbDL

# From source
git clone https://github.com/Jo0X01/Anime3rbDL.git
cd Anime3rbDL
pip install -r requirements.txt
pip install -e .
```

**Requirements:** Python 3.8+, Chrome/Edge browser.

## 💻 CLI Usage

### Basic Commands

```bash
# Help
Anime3rbDL --help

# Search anime
Anime3rbDL "Naruto"

# Latest releases
Anime3rbDL --latest

# Download episodes
Anime3rbDL "One Piece" --download-parts 1-5 --res mid --output-dir ./downloads
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `query` | Anime search query or URL | `"Naruto"` or `"https://anime3rb.com/titles/naruto"` |
| `-l, --latest` | Fetch latest releases | |
| `-v, --verbose` | Verbose logging | |
| `-lf, --log-file` | Log to file | `--log-file anime.log` |
| `-nl, --no-logger` | Disable logging | |
| `--no-warn` | Suppress warning messages | |
| `--no-color` | Disable colored output | |
| `--debug` | Show full errors | |
| `-t, --timeout` | Request timeout (s) | `--timeout 60` |
| `-ct, --cf-token` | Manual Cloudflare token | `--cf-token "token"` |
| `-ua, --user-agent` | Custom User-Agent | `--user-agent "Mozilla/..."` |
| `-p, --proxy` | Proxy server | `--proxy "http://127.0.0.1:8080"` |
| `-e, --on-expire-token` | CF handling: `ask/auto/ignore` | `--on-expire-token auto` |
| `--login` | Login (email password) | `--login user@example.com pass` |
| `--register` | Register (username email password) | `--register user user@example.com pass` |
| `-ds, --deep-search` | Deep search mode | |
| `-si, --search-index` | Select search result | `--search-index 1` |
| `-n, --max-results` | Max search results | `--max-results 10` |
| `-d, --download-parts` | Episodes (e.g., 1-3,5) | `--download-parts 1-3,5` |
| `-c, --download-chunks` | Download chunks | |
| `-m, --max-workers` | Max workers | `--max-workers 8` |
| `-r, --res` | Resolution: `low/mid/high` | `--res high` |
| `-dn, --download-now` | Download immediately | |
| `-o, --output-dir` | Output directory | `--output-dir ./anime` |
| `--hide-browser` | Hide browser for CF solving | |
| `--binary-path` | Browser binary path | `--binary-path /usr/bin/chrome` |
| `--user-dir` | Browser user dir | |
| `--ws-addr` | WebSocket for browser | |

### Examples

```bash
# Verbose search and download
Anime3rbDL "Demon Slayer" --download-parts 1-3 --res mid --verbose --output-dir ./downloads

# With proxy and timeout
Anime3rbDL "Jujutsu Kaisen" --proxy "socks5://127.0.0.1:1080" --timeout 120

# Manual CF token
Anime3rbDL "Tokyo Ghoul" --cf-token "your_token" --user-agent "your_ua"

# Auto CF solving
Anime3rbDL "My Hero Academia" --on-expire-token auto --hide-browser --timeout 180
```

## 🐍 Python API

### Basic Usage

```python
from Anime3rbDL import Anime3rbDL, Config

# Initialize
client = Anime3rbDL(enable_logger=True, verbose=True, log_file="log.txt")

# Configure
Config.timeout = 60
Config.HTTPProxy = "http://127.0.0.1:8080"

# Search
results = client.search("Naruto", max_results=10)

# Get info
episodes = client.get_info("1-3", res="mid")

# Download
files = client.download(path="./downloads", res="mid")
```

### Project Structure

```
Anime3rbDL/
├── __init__.py      # Main API class and entry point
├── __main__.py      # CLI interface implementation
├── bot.py          # Cloudflare solver with PyDoll
├── client.py       # HTTP client with cloudscraper integration
├── config.py       # Global configuration and caching
├── downloader.py   # Multi-threaded download manager with fallback
├── logger.py       # Custom logging system with colored output
├── parser.py       # HTML/JSON parsing utilities
├── enums.py        # Data models and type definitions
└── exceptions.py   # Custom exception classes
```

### Main Methods

#### `Anime3rbDL(enable_logger=True, verbose=False, log_file=None)`
Initialize the client.

#### `login(email, password)`
Login to Anime3rb. Returns bool.

```python
success = client.login("user@example.com", "password")
```

#### `register(username, email, password)`
Register account. Returns bool.

```python
success = client.register("user", "user@example.com", "password")
```

#### `search(query=None, index=None, max_results=None, fast_mode=True)`
Search anime or fetch latest. Returns search data.

```python
# Search
results = client.search("Attack on Titan", max_results=10)

# Latest
latest = client.search()
```

#### `get_info(download_parts="all", res="low", download=False, path=".")`
Get episode info, optionally download. Returns episodes or file paths.

```python
# Info only
episodes = client.get_info("1-3", res="mid")

# Download
files = client.get_info("1-3", res="mid", download=True, path="./downloads")
```

#### `download(path=".", res="low")`
Download cached episodes. Returns file paths.

```python
files = client.download(path="./anime", res="high")
```

#### `get_latest(max_fetch=30)`
Fetch latest releases. Returns list.

```python
latest = client.get_latest(20)
```

## ⚙️ Configuration

Use the `Config` class for global settings:

```python
from Anime3rbDL import Config

# Network
Config.timeout = 60
Config.HTTPProxy = "socks5://127.0.0.1:1080"
Config.UserAgent = "Custom UA"

# Cloudflare
Config.SolveWay = "auto"  # ask/auto/ignore
Config.CloudFlareToken = "token"

# Download
Config.MaxWorkers = 8
Config.DownloadChunks = 131072

# Logging
Config.LoggerV = True
Config.LogFile = "log.txt"
Config.no_warn = False  # Suppress warnings
```

### Advanced Logging System

Anime3rbDL includes a custom logging system with the following features:

- **Colored Console Output**: Different colors for each log level (DEBUG: Cyan, INFO: Green, WARNING: Yellow, ERROR: Red, CRITICAL: Magenta)
- **Verbose Mode**: Detailed DEBUG logging with timestamps, module names, and line numbers
- **File Logging**: Save logs to file with proper formatting
- **Warning Suppression**: Use `Config.no_warn = True` to suppress WARNING messages
- **Performance Optimized**: Built on Python's standard logging module

#### Logging Configuration

```python
from Anime3rbDL import Config

# Enable verbose logging
Config.LoggerV = True

# Save logs to file
Config.LogFile = "anime_downloader.log"

# Suppress warning messages
Config.no_warn = True

# Initialize logger
Config.setup_logger()
```

#### CLI Logging Options

| Option | Description | Example |
|--------|-------------|---------|
| `-v, --verbose` | Enable verbose (debug) logging | `--verbose` |
| `--log-file` | Save logs to file | `--log-file anime.log` |
| `--no-logger` | Disable logging entirely | `--no-logger` |
| `--no-warn` | Suppress warning messages | `--no-warn` |
| `--no-color` | Disable colored output | `--no-color` |

#### Logging Levels

- **DEBUG**: Detailed diagnostic information (enabled with `--verbose`)
- **INFO**: General information about operations
- **WARNING**: Warning messages (suppressed with `--no-warn`)
- **ERROR**: Error conditions that stop execution


## 🔧 Troubleshooting

### Common Issues

**Cloudflare Blocking:**
- Use `--on-expire-token auto` for automation.
- Or `--on-expire-token ask` for manual token input.
- Increase `--timeout` to 180+.

**Slow/Failed Downloads:**
- Increase `--timeout`.
- Use `--proxy` if needed.
- Reduce `--max-workers` if rate-limited.

**Authentication Errors:**
- Verify credentials.
- Clear browser cache.
- Check account status on site.

**Browser Automation Fails:**
- Ensure Chrome/Edge installed.
- Try `--hide-browser` or manual mode.
- Check system resources.

**Resume Downloads:**
- Re-run the same command; resume is automatic.

### Debug Mode
Enable `--debug` for full tracebacks, `-v` for verbose logs.



## 📄 License

MIT License © 2025 Mr.Jo0x01

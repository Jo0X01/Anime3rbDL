<div align="center">

# 🎌 Anime3rbDL

[![PyPI version](https://img.shields.io/pypi/v/Anime3rbDL.svg?logo=pypi&logoColor=white)](https://pypi.org/project/Anime3rbDL/)
[![Python versions](https://img.shields.io/pypi/pyversions/Anime3rbDL.svg)](https://pypi.org/project/Anime3rbDL/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/Jo0X01/Anime3rbDL/blob/main/LICENSE)

*A powerful, intelligent, and feature-rich command-line tool and Python library for **searching, retrieving, and downloading anime episodes** from **[Anime3rb](https://anime3rb.com)** with advanced Cloudflare bypass capabilities powered by automated browser technology.*

<p align="center">
  <img src="Anime3rbDL.ico" alt="Anime3rbDL Logo" width="200" height="200">
</p>

<div align="center">

**Made with ❤️ for the anime community**

[⭐ Star on GitHub](https://github.com/Jo0X01/Anime3rbDL) • [🐛 Report Issues](https://github.com/Jo0X01/Anime3rbDL/issues) • [📖 Wiki](doc.md) • [💬 Discussions](https://github.com/Jo0X01/Anime3rbDL/discussions)

</div>

<div align="left">

## ✨ Key Features

- 🔍 **Smart Search Engine** - Advanced search by name or direct URL with intelligent parsing and caching
- 📥 **Bulk Download Manager** - Download specific episodes, ranges, or entire series with resume support
- 🎥 **Multi-Resolution Support** - High-quality downloads in 480p, 720p, and 1080p resolutions
- 🤖 **Automated Cloudflare Bypass** - State-of-the-art browser automation for seamless access to protected content
- 🔐 **User Authentication System** - Full login and registration support with secure credential handling
- ⚡ **High-Performance Architecture** - Multi-threaded downloads with intelligent retry mechanisms
- 🛠️ **Flexible Dual Interface** - Both powerful CLI and comprehensive Python API
- 🌐 **Proxy & Network Support** - HTTP/SOCKS proxy compatibility with custom timeout configurations
- 📊 **Rich Metadata Extraction** - Detailed episode information, file sizes, and quality metrics
- 🎯 **Precision Episode Selection** - Advanced filtering and selection for targeted downloads

</div>
</div>

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [💻 Usage Guide](#-usage-guide)
  - [Command Line Interface](#command-line-interface)
  - [Python API](#python-api)
- [🤖 Advanced Cloudflare Handling Using PyDoll](#-advanced-cloudflare-handling)
- [⚙️ Configuration & Customization](#️-configuration--customization)
- [🔧 Troubleshooting & FAQ](#-troubleshooting--faq)
- [📝 Development & Contributing](#-development--contributing)
- [🙏 Special Thanks](#-special-thanks)
- [📄 License & Disclaimer](#-license--disclaimer)

---

## 🚀 Quick Start

Get up and running in seconds with our streamlined installation and basic usage:

```bash
# Install the package
pip install Anime3rbDL

# Search and download Naruto episodes 1-3 in 720p quality
Anime3rbDL "Naruto" --download-parts 1-3 --res mid --timeout 60
```

---

## 📦 Installation

### Option 1: PyPI Installation (Recommended)
```bash
pip install Anime3rbDL
```

### Option 2: Development Installation
```bash
git clone https://github.com/Jo0X01/Anime3rbDL.git
cd Anime3rbDL
pip install -r requirements.txt
pip install -e .
```

### System Requirements
- **Python 3.8+**
- **Chrome or Edge browser** (for automated Cloudflare solving)
- **Internet connection** with sufficient bandwidth for downloads

---

## 💻 Usage Guide

### Command Line Interface

#### Basic Commands

```bash
# Display help and available options
Anime3rbDL --help or Anime3rbDL

# Search for anime by name
Anime3rbDL "Attack on Titan"

# Fetch latest anime releases
Anime3rbDL --latest

# Download specific episodes with custom settings
Anime3rbDL "One Piece" --download-parts 1-5,10 --res high --output-dir ./anime_downloads

# Use direct URL for precise targeting
Anime3rbDL "https://anime3rb.com/titles/one-piece" --download-parts 10-15 --timeout 120
```

#### Advanced Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--latest` | Explicitly fetch latest anime releases | |
| `--download-parts` | Specify episodes to download | `1-3,5,8` or `all` |
| `--res` | Set video resolution | `low` (480p), `mid` (720p), `high` (1080p) |
| `--output-dir` | Custom download directory | `/path/to/your/downloads` |
| `--timeout` | Request timeout in seconds | `60` (default: 30) |
| `--proxy` | HTTP/SOCKS proxy server | `http://127.0.0.1:8080` or `socks5://127.0.0.1:1080` |
| `--cf-token` | Manual Cloudflare clearance token | `your_cf_clearance_token_here` |
| `--on-expire-token` | Cloudflare handling strategy | `ask`, `auto`, `ignore` |
| `--user-agent` | Custom User-Agent string | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| `-v, --verbose` | Enable detailed logging | |
| `--log-file` | Save logs to file | `anime_downloader.log` |
| `--no-color` | Disable colored output | |

#### Cloudflare Token Management

```bash
# Interactive manual solving (opens browser for token extraction)
Anime3rbDL "Demon Slayer" --on-expire-token ask

# Fully automated solving (requires browser automation setup)
Anime3rbDL "Jujutsu Kaisen" --on-expire-token auto

# Bypass Cloudflare handling entirely
Anime3rbDL "Tokyo Ghoul" --on-expire-token ignore
```

### Python API

#### Basic Implementation

```python
from Anime3rbDL import Anime3rbDL, Config

# Initialize client with custom settings
client = Anime3rbDL(
    enable_logger=True,
    verbose=True,
    log_file="anime_downloads.log"
)

# Configure global settings
Config.timeout = 60
Config.SolveWay = "auto"
Config.HTTPProxy = "http://127.0.0.1:8080"

# Search for anime
search_results = client.search("Naruto", max_results=10)

# Get detailed episode information
episode_info = client.get_info("1-3", res="mid")

# Download episodes to specified directory
downloaded_files = client.download(path="./downloads", res="mid")
```

#### Advanced API Usage

```python
from Anime3rbDL import Anime3rbDL, Config, Cache

# Create client with comprehensive configuration
client = Anime3rbDL(
    enable_logger=True,
    verbose=True,
    log_file="detailed_logs.log"
)

# Set up proxy and timeout
Config.HTTPProxy = "socks5://127.0.0.1:1080"
Config.timeout = 120
Config.MaxWorkers = 8  # Increase download threads

# Authenticate user account
login_success = client.login("your_email@example.com", "your_password")

# Register new account if needed
# registration_success = client.register("username", "email@example.com", "password")

# Perform search with filtering
results = client.search("Attack on Titan", max_results=5, fast_mode=False)

# Get comprehensive episode data
client.get_info("1-10", res="high")

# Access cached data
print(f"Anime Title: {Cache.ANIME_TITLE}")
print(f"Total Episodes: {len(Cache.EpisodesDownloadData)}")
print(f"Total Size: {Cache.TotalSize.getByVal('high')}")

# Download with progress tracking
downloaded_files = client.download(path="/mnt/nas/anime", res="high")
```

---

## 🤖 Advanced Cloudflare Handling

Anime3rbDL features a cutting-edge **Cloudflare bypass system** that leverages advanced browser automation to provide seamless access to protected content. This system is designed to handle modern anti-bot protections intelligently and efficiently.

### How the System Works

The integrated `CFSolver` class utilizes **PyDoll** with Chromium-based browsers to:

1. **Launch Temporary Browser Instance** - Creates an isolated Chrome or Edge browser session
2. **Navigate to Target URL** - Loads the protected page while monitoring for challenges
3. **Intelligent Challenge Detection** - Automatically identifies and waits for Cloudflare challenges
4. **Automated Solving Process** - Uses real browser rendering to solve challenges transparently
5. **Token Extraction** - Captures the `cf_clearance` cookie and User-Agent string
6. **Seamless Integration** - Provides extracted credentials to the HTTP client for authenticated requests

### Cloudflare Solving Modes

| Mode | Description | Best For | Automation Level |
|------|-------------|----------|------------------|
| **`ask`** | Interactive mode - opens browser and prompts for manual token input | Users who prefer manual control | Manual |
| **`auto`** | Fully automated - browser runs in background to solve challenges | Most users seeking convenience | Fully Automated |
| **`ignore`** | Bypass mode - skips Cloudflare solving entirely | Users with existing valid tokens | None |

### Browser Automation Setup

For optimal performance with `auto` mode:

#### Prerequisites
- **Chrome or Edge Browser** installed on your system
- **PyDoll** dependency (automatically installed with Anime3rbDL)
- **Sufficient system resources** (RAM: 2GB+, CPU cores: 2+)

#### Configuration Options

```python
from Anime3rbDL.bot import CFSolver

# Create solver with custom settings
solver = CFSolver(
    browser_type='chrome',  # or 'edge'
    proxy='http://127.0.0.1:8080',
    timeout=60,
    hide_browser=True,  # Run browser in background
    binary_path='/usr/bin/google-chrome',
    user_dir='/tmp/chrome_profile'
)

# Solve Cloudflare challenge
token, user_agent = solver.solve('https://anime3rb.com/search?q=anime')
```

### Manual Token Usage

For users who prefer manual control:

1. **Navigate to Any Protection Endpoint Website** - Open https://anime3rb.com in your browser
2. **Solve Challenges** - Complete any Cloudflare verification steps
3. **Extract Token & UserAgent** - Copy the `cf_clearance` cookie value from browser dev tools
4. **Apply Token** - Use the extracted token with `--cf-token` flag

```bash
Anime3rbDL "Anime Title" --cf-token "your_extracted_cf_clearance_token" -ue "your_browser_user_agent"
```

### Troubleshooting Cloudflare Issues

**Problem**: Browser automation fails
```bash
# Solutions:
# 1. Ensure Chrome/Edge is installed and up-to-date
# 2. Check system resources (close other applications)
# 3. Try manual mode as fallback
Anime3rbDL "Anime Title" --on-expire-token ask
```

**Problem**: Token expires frequently
```bash
# Solutions:
# 1. Use auto mode for automatic renewal
# 2. Increase timeout values
# 3. Consider using a stable proxy
Anime3rbDL "Anime Title" --on-expire-token auto --timeout 120 --proxy "http://proxy:port"
```

---

## ⚙️ Configuration & Customization

### Global Configuration Object

```python
from Anime3rbDL import Config

# Network Settings
Config.timeout = 30  # Request timeout in seconds
Config.HTTPProxy = "http://127.0.0.1:8080"  # Proxy server
Config.UserAgent = "Custom User Agent String"  # Custom User-Agent

# Cloudflare Settings
Config.SolveWay = "auto"  # "ask", "auto", or "ignore"
Config.CloudFlareToken = "your_token_here"  # Manual token

# Download Settings
Config.MaxWorkers = 4  # Number of download threads
Config.DownloadChunks = 8192 * 8  # Chunk size for downloads

# Logging Settings
Config.LoggerV = True  # Enable verbose logging
Config.LogFile = "anime_downloader.log"  # Log file path
Config.no_warn = False  # Suppress warning messages
```

### Advanced Logging System

Anime3rbDL features a custom logging system with colored console output, file logging, and warning suppression capabilities.

#### Logging Features
- **Colored Console Output**: DEBUG (Cyan), INFO (Green), WARNING (Yellow), ERROR (Red), CRITICAL (Magenta)
- **Verbose Mode**: Enable detailed DEBUG logging with timestamps, module names, and line numbers
- **File Logging**: Save logs to file with optional rotation
- **Warning Suppression**: Use `--no-warn` flag to suppress WARNING level messages
- **Performance Optimized**: Uses Python's standard logging module for efficiency

#### Logging Configuration

```python
from Anime3rbDL import Config

# Enable verbose logging (shows DEBUG messages)
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

#### Logging Levels

- **DEBUG**: Detailed diagnostic information (enabled with `--verbose`)
- **INFO**: General information about operations
- **WARNING**: Warning messages (suppressed with `--no-warn`)
- **ERROR**: Error conditions stop execution


## 🔧 Troubleshooting & FAQ

### Common Issues

**Q: Downloads are slow or failing**
```bash
# A: Increase timeout and use proxy
Anime3rbDL "Anime Title" --timeout 120 --proxy "http://127.0.0.1:8080"
```

**Q: Cloudflare blocks are persistent**
```bash
# A: Use automated solving with increased timeout
Anime3rbDL "Anime Title" --on-expire-token auto --timeout 180
```

**Q: Incomplete downloads**
```bash
# A: The downloader supports resume - re-run the same command
Anime3rbDL "Anime Title" --download-parts 1-5
```

**Q: Browser automation not working**
```bash
# A: Check browser installation and try manual mode
Anime3rbDL "Anime Title" --on-expire-token ask
```

---

## 📝 Development & Contributing

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

### Development Setup

```bash
git clone https://github.com/Jo0X01/Anime3rbDL.git
cd Anime3rbDL
pip install -r requirements.txt
pip install -e .  # Install in development mode

# Run tests
python -c "import Anime3rbDL; print('Import successful')"

# Test CLI
python -m Anime3rbDL --help
```

### Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper documentation
4. Add tests if applicable
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 🙏 Special Thanks

A special thanks to the **PyDoll framework** for providing the robust browser automation capabilities that power Anime3rbDL's advanced Cloudflare bypass system. PyDoll enables seamless interaction with Chromium-based browsers, making it possible to handle complex anti-bot protections automatically.

For more detailed documentation on usage, methods, and advanced features, please refer to [doc.md](doc.md).

---

## 📄 License & Disclaimer

**MIT License** © 2025 Mr.Jo0x01

This project is intended for **educational and personal use only**. Users are responsible for complying with all applicable laws and regulations regarding content access and download. The developers are not responsible for any misuse of this software.

Please respect the intellectual property rights of content creators and only download material you have permission to access.

---

<div align="center">

**Made with ❤️ for the anime community**

[⭐ Star on GitHub](https://github.com/Jo0X01/Anime3rbDL) • [🐛 Report Issues](https://github.com/Jo0X01/Anime3rbDL/issues) • [📖 Wiki](doc.md) • [💬 Discussions](https://github.com/Jo0X01/Anime3rbDL/discussions)

</div>

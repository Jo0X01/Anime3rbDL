from typing import Optional
import ctypes
import cloudscraper
from Anime3rbDL.bot import CFSolver
from Anime3rbDL.config import Config
from requests.exceptions import RequestException
import os
import platform
import webbrowser
from Anime3rbDL.downloader import Downloader
from Anime3rbDL.enums import ResoultionData


# ------------------- Helpers -------------------


def _is_elevated() -> bool:
    """
    Check if the current process has admin privileges on Windows.

    Returns:
        bool: True if elevated, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _manual_cf_input(url: str) -> Optional[str]:
    """Prompt user to manually solve Cloudflare challenge and input token.

    Adapts instructions based on platform and display availability:
    - GUI environments: Opens browser and guides through DevTools.
    - Headless environments: Prints URL and manual steps.
    Collects cf_clearance token and optional User-Agent update.

    Args:
        url (str): Cloudflare-protected URL to solve.

    Returns:
        Optional[str]: cf_clearance token if provided, None otherwise.
    """
    system = platform.system().lower()
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    is_termux = "com.termux" in os.environ.get("PREFIX", "").lower()

    print("\n[Cloudflare Challenge Detected]\n")

    if system in ("windows", "linux") and has_display and not is_termux:
        print("Instructions:")
        print(" 1. A browser window will open shortly.")
        print(" 2. Wait until the page fully loads and Cloudflare passes.")
        print(
            " 3. Open DevTools → Application/Storage → Cookies → copy 'cf_clearance'."
        )
        print(" 4. In DevTools → Network → copy 'User-Agent'.\n")
        input("Press Enter to open your browser... ")
        webbrowser.open(url)

    else:
        print("This environment does not support automatic browser opening.")
        print("Please copy this link into a real browser on any device:")
        print(f"\n   {url}\n")
        print("Steps:")
        print(" 1. Let the page load fully.")
        print(
            " 2. Open DevTools → Application/Storage → Cookies → copy 'cf_clearance'."
        )
        print(" 3. In DevTools → Network → copy 'User-Agent'.\n")

    token = input("Paste cf_clearance token >>> ").strip()
    if not token:
        print("[i] No token entered, continuing without Cloudflare clearance.")
        return None

    ua = input(
        "Paste User-Agent from browser (or press Enter to keep default) >>> "
    ).strip()
    if ua:
        Config.UserAgent = ua
        print(f"[i] Updated User-Agent: {ua}")

    return token


def solve_cf_clearance(solver: CFSolver, url: str) -> Optional[str]:
    """Solve Cloudflare challenge for URL based on configured method.

    Supports three solving modes via Config.SolveWay:
    - "ignore": Skip solving entirely, log warning.
    - "ask": Prompt user to manually obtain and input token.
    - "auto": Attempt automated solving with browser, fallback to manual.

    Handles elevated privileges (skips auto) and logs process details.

    Args:
        solver (CFSolver): Automated solver instance.
        url (str): URL requiring Cloudflare clearance.

    Returns:
        Optional[str]: cf_clearance token on success, None on failure/skip.
    """
    if Config.LoggerV:
        Config.logger.debug(f"Solving Cloudflare for URL: {url}")
        Config.logger.debug(f"Solve method: {Config.SolveWay}")

    if Config.SolveWay == "ignore":
        Config.logger.warning("Ignoring Cloudflare protection, may fail.")
        if Config.LoggerV:
            Config.logger.debug("Cloudflare solving set to ignore")
        return None

    if Config.SolveWay == "ask":
        if Config.LoggerV:
            Config.logger.debug("Using manual Cloudflare solving method")
        return _manual_cf_input(url)

    if Config.SolveWay == "auto":
        if _is_elevated():
            Config.logger.warning(
                "Process running with admin privileges — automation may fail."
            )
            if Config.LoggerV:
                Config.logger.debug("Process elevated, skipping auto solve")
            return None

        try:
            Config.logger.info("Attempting automatic Cloudflare solve")
            Config.logger.warning(
                "Attempting automatic Cloudflare solve (may require manual action)..."
            )
            if Config.LoggerV:
                Config.logger.debug("Attempting automatic Cloudflare solve")
            token, ua = solver.solve(url)
            Config.UserAgent = ua
            if Config.LoggerV:
                Config.logger.debug("Automatic Cloudflare solve successful")
            solver.close_browser()
            return token
        except Exception as e:
            Config.logger.error(f"Auto solver failed: {e}, falling back to manual")
            Config.logger.warning(f"Auto solver failed: {e}")
            if Config.LoggerV:
                Config.logger.debug(f"Auto solver failed: {e}, falling back to manual")
            return _manual_cf_input(url)

    if Config.LoggerV:
        Config.logger.debug("Unknown solve method, returning None")
    return None


# ------------------- Client -------------------


class Anime3rbHTTPClient:
    """HTTP client for Anime3rbDL with Cloudflare bypass capabilities.

    Manages cloudscraper session and CFSolver browser for handling protected sites.
    Provides methods for GET/POST/HEAD requests with automatic CF solving.
    Handles proxy configuration, User-Agent setting, and token management.

    Class Attributes:
        scraper (Optional[cloudscraper.CloudScraper]): Main HTTP session.
        driver (Optional[CFSolver]): Browser-based CF solver.
    """

    scraper: Optional[cloudscraper.CloudScraper] = None
    driver: Optional[CFSolver] = None

    # --- Setup ---

    @classmethod
    def init_scraper(cls) -> None:
        """Initialize cloudscraper session and CFSolver browser instance.

        Creates scraper with Chrome/Edge browser emulation, sets proxy if configured,
        applies existing CF token and User-Agent. Initializes CFSolver for auto-solving.

        Logs configuration details when verbose logging enabled.
        """
        if Config.LoggerV:
            Config.logger.debug("Initializing HTTP client scraper")

        proxy = Config.HTTPProxy
        ua = Config.UserAgent
        default_token = Config.CloudFlareToken

        if Config.LoggerV:
            Config.logger.debug(
                f"HTTP client config - Proxy: {proxy}, User-Agent: {ua}, Token: {'***' if default_token else 'None'}"
            )

        browser_opts = {"browser": "chrome", "platform": "windows", "mobile": False}
        cls.driver = CFSolver(proxy)

        if proxy:
            cls.scraper = cloudscraper.create_scraper(
                browser=browser_opts, proxies={"http": proxy, "https": proxy}
            )
            Config.logger.info(f"Using proxy: {proxy}")
            if Config.LoggerV:
                Config.logger.debug(f"Created scraper with proxy configuration")
        else:
            cls.scraper = cloudscraper.create_scraper(browser=browser_opts)
            if Config.LoggerV:
                Config.logger.debug("Created scraper without proxy")

        # Only set clearance if we actually have one
        if default_token:
            cls.scraper.cookies.set("cf_clearance", default_token)
            if Config.LoggerV:
                Config.logger.debug("Set existing Cloudflare token")

        cls.scraper.headers.update({"User-Agent": ua})
        
        if Config.LoggerV:
            Config.logger.debug("HTTP client initialization completed")

    # --- CF Detection ---

    @staticmethod
    def _is_protected(response) -> bool:
        """Check if HTTP response indicates Cloudflare protection.

        Detects CF challenges by status codes (403, 503) or presence of
        "Just a moment..." title in response content.

        Args:
            response: HTTP response object to check.

        Returns:
            bool: True if Cloudflare challenge detected, False otherwise.
        """
        return (
            response.status_code in (403, 503)
            or "<title>Just a moment...</title>" in response.text
        )

    # --- Internal Requests ---

    @classmethod
    def _request(cls, method: str, url: str, headers=None, payload=None, stream=False):
        """Perform raw HTTP request using cloudscraper session.

        Supports GET, POST, HEAD methods with optional headers, payload, and streaming.
        Uses configured timeout from Config.timeout.

        Args:
            method (str): HTTP method ('GET', 'POST', 'HEAD').
            url (str): Target URL.
            headers (dict, optional): Additional headers. Defaults to None.
            payload (dict, optional): JSON payload for POST. Defaults to None.
            stream (bool, optional): Enable response streaming. Defaults to False.

        Returns:
            Response: cloudscraper response object.
        """
        if method == "GET":
            return cls.scraper.get(
                url,
                headers=headers,
                allow_redirects=True,
                stream=stream,
                timeout=Config.timeout,
            )
        if method == "POST":
            return cls.scraper.post(
                url,
                json=payload,
                allow_redirects=True,
                headers=headers,
                timeout=Config.timeout,
            )
        if method == "HEAD":
            return cls.scraper.head(
                url, headers=headers, allow_redirects=True, timeout=Config.timeout
            )

    @classmethod
    def _ensure_cf(
        cls, method: str, url: str, headers=None, payload=None, stream=False
    ):
        """Ensure Cloudflare clearance for request, solving if protected.

        Initializes scraper if needed, performs initial request to detect CF,
        solves challenge if detected, then retries the request with token.

        Args:
            method (str): HTTP method.
            url (str): Target URL.
            headers (dict, optional): Request headers.
            payload (dict, optional): Request payload.
            stream (bool): Streaming mode.

        Returns:
            Response: Successful response or None on failure.
        """
        headers = headers or {}
        payload = payload or {}

        if Config.LoggerV:
            Config.logger.debug("Ensuring Cloudflare clearance for request")

        if cls.scraper is None or cls.driver is None:
            if Config.LoggerV:
                Config.logger.debug("Scraper not initialized, initializing now")
            cls.init_scraper()

        try:
            if Config.LoggerV:
                Config.logger.debug(
                    "Making initial request to check for Cloudflare protection"
                )
            resp = cls._request(method, url, headers, payload, stream)
        except RequestException as e:
            Config.logger.warning(f"HTTP request failed: {e}")
            if Config.LoggerV:
                Config.logger.debug(f"Request exception: {e}")
            return None

        if resp is None:
            Config.logger.warning(f"[ensure_cf] Empty response from {url}")
            if Config.LoggerV:
                Config.logger.debug("Received empty response from server")
            return None

        if not cls._is_protected(resp):
            if Config.LoggerV:
                Config.logger.debug(
                    "No Cloudflare protection detected, returning response"
                )
            return resp

        # Solve Cloudflare
        Config.logger.warning("Cloudflare protection detected, solving...")
        if Config.LoggerV:
            Config.logger.debug(
                "Cloudflare protection detected, initiating solving process"
            )

        token = solve_cf_clearance(cls.driver, url)
        if not token:
            if Config.LoggerV:
                Config.logger.debug("Cloudflare solving failed or was skipped")
            return None

        cls.scraper.cookies.set("cf_clearance", token)
        cls.scraper.headers.update({"User-Agent": Config.UserAgent})

        if Config.LoggerV:
            Config.logger.debug("Retrying request with Cloudflare token")

        try:
            return cls._request(method, url, headers, payload, stream)
        except RequestException as e:
            Config.logger.warning(f"HTTP request failed after CF solve: {e}")
            if Config.LoggerV:
                Config.logger.debug(f"Request failed after Cloudflare solve: {e}")
            return None

    # --- Public API ---

    @classmethod
    def make_request(
        cls, method: str, url: str, headers=None, payload=None, stream=False
    ):
        """Make HTTP request with automatic Cloudflare solving and retry logic.

        Calls _ensure_cf to handle CF challenges, retries on token expiration (403/503).
        Accepts success codes: 200 (OK), 206 (Partial), 302 (Redirect), 429 (Rate limit).

        Args:
            method (str): HTTP method ('GET', 'POST', 'HEAD').
            url (str): Target URL.
            headers (dict, optional): Request headers.
            payload (dict, optional): Request payload for POST.
            stream (bool): Enable streaming.

        Returns:
            Response: Response object on success, None on failure.
        """
        if Config.LoggerV:
            Config.logger.debug(f"Making {method} request to: {url}")
            if payload:
                Config.logger.debug(f"Request payload: {payload}")
            if headers:
                Config.logger.debug(f"Request headers: {headers}")

        resp = cls._ensure_cf(method, url, headers, payload, stream)
        if resp is None:
            Config.logger.warning(f"[make_request] No response from {url}")
            if Config.LoggerV:
                Config.logger.debug(f"Request failed - no response received")
            return None

        if Config.LoggerV:
            Config.logger.debug(
                f"Response status: {resp.status_code}, Content-Type: {resp.headers.get('content-type', 'unknown')}"
            )

        if resp.status_code in (403, 503):
            Config.logger.warning("Token expired, retrying...")
            if Config.LoggerV:
                Config.logger.debug("Retrying request due to token expiration")
            resp = cls._ensure_cf(method, url, headers, payload, stream)

        if resp and resp.status_code in (200, 206, 302, 429):
            if Config.LoggerV:
                Config.logger.debug(
                    f"Request successful with status {resp.status_code}"
                )
            return resp

        Config.logger.warning(
            f"[make_request] Unexpected status {resp.status_code} for {url}"
        )
        if Config.LoggerV:
            Config.logger.debug(
                f"Request failed with unexpected status {resp.status_code}"
            )
        return None

    @classmethod
    def get_req(cls, url: str, headers=None, stream=False):
        """Send GET request and return content or response.

        Args:
            url (str): Target URL.
            headers (dict, optional): Request headers.
            stream (bool): Return response object if True, content bytes if False.

        Returns:
            Response or bytes: Response object if stream=True, content bytes otherwise.
        """
        resp = cls.make_request("GET", url, headers, stream=stream)
        return resp if stream else (resp.content if resp else None)

    @classmethod
    def post_req(cls, url: str, payload=None, headers=None, return_response=False):
        """Send POST request with JSON payload.

        Args:
            url (str): Target URL.
            payload (dict, optional): JSON payload to send.
            headers (dict, optional): Request headers.
            return_response (bool): Return response object if True, parsed JSON if False.

        Returns:
            Response or dict: Response object or parsed JSON data.
        """
        resp = cls.make_request("POST", url, headers, payload)
        if not resp:
            return None
        return resp if return_response else resp.json()

    @classmethod
    def head_req(cls, url: str, headers=None):
        """Send HEAD request to check resource without downloading.

        Args:
            url (str): Target URL.
            headers (dict, optional): Request headers.

        Returns:
            Response: HEAD response object.
        """
        return cls.make_request("HEAD", url, headers)

    @classmethod
    def stream_req(cls, url: str, headers=None):
        """Send streaming GET request for large downloads.

        Validates response is not blocked (403/503) or HTML error page.

        Args:
            url (str): Download URL.
            headers (dict, optional): Request headers.

        Returns:
            Response: Streaming response object, or None if blocked/invalid.
        """
        resp = cls.make_request("GET", url, headers, stream=True)
        if not resp:
            return None
        if resp.status_code in (403, 503) or resp.headers.get(
            "content-type", ""
        ).startswith("text/html"):
            Config.logger.warning("Blocked or invalid link.")
            return None
        return resp

    @classmethod
    def download_file(cls, cls_object: ResoultionData, output_dir: str):
        """Download file using Downloader class with current scraper session.

        Initializes scraper if not already done, creates Downloader instance
        with the cloudscraper session for handling protected downloads.

        Args:
            cls_object (ResoultionData): Download metadata (URL, filename, size).
            output_dir (str): Directory to save downloaded file.

        Returns:
            str: Path to downloaded file.
        """
        if cls.scraper is None:
            cls.init_scraper()
        return Downloader(cls.scraper).download(cls_object, output_dir)

    @classmethod
    def close_browser(cls):
        """Close CFSolver browser instance and clean up resources.

        Safely terminates the browser driver, sets reference to None.
        Also attempts to kill any orphaned browser processes.
        Called automatically on exit but can be invoked manually.
        """
        if cls.driver is not None:
            if Config.LoggerV:
                Config.logger.debug("Closing browser instance")
            try:
                cls.driver.close_browser()
                cls.driver = None
                if Config.LoggerV:
                    Config.logger.debug("Browser instance closed successfully")
            except Exception as e:
                if Config.LoggerV:
                    Config.logger.debug(f"Error closing browser: {e}")
                # Reset driver reference even if close fails
                cls.driver = None

        # Also try to clean up any remaining browser processes that might be related
        try:
            import psutil
            import os

            # Look for browser processes that might be related to our script
            current_pid = os.getpid()
            for proc in psutil.process_iter(["pid", "name", "ppid"]):
                try:
                    # Check if this is a browser process whose parent is our script
                    if (
                        proc.info["ppid"] == current_pid
                        and proc.info["name"]
                        and (
                            "chrome" in proc.info["name"].lower()
                            or "edge" in proc.info["name"].lower()
                            or "chromium" in proc.info["name"].lower()
                        )
                    ):

                        if Config.LoggerV:
                            Config.logger.debug(
                                f"Terminating orphaned browser process: {proc.info['name']} (PID: {proc.info['pid']})"
                            )

                        try:
                            psutil.Process(proc.info["pid"]).terminate()
                        except psutil.NoSuchProcess:
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            if Config.LoggerV:
                Config.logger.debug(f"Error during process cleanup: {e}")
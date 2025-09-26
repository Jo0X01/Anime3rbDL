import asyncio
import tempfile
import signal
import sys
import os
import atexit
import psutil
from pydoll.browser import Edge, Chrome
from pydoll.browser.options import ChromiumOptions as Options

from Anime3rbDL.config import Config

class CFSolver:
    """
    Cloudflare Solver using PyDoll and a Chromium-based browser.

    This class launches a temporary browser instance, navigates to a given URL,
    and waits until the Cloudflare challenge (`cf_clearance` cookie) is solved.
    Once solved, it retrieves the clearance token and the browser's User-Agent.

    Args:
        proxy (str, optional): Proxy server in format `http://ip:port` or `socks5://ip:port`.
        timeout (int, optional): Maximum time in seconds to wait for Cloudflare to resolve.
    """

    def __init__(self,
                 browser_type:str='edge',
                 proxy: str = None,
                 timeout: int = 30,
                 hide_browser:bool=False,
                 binary_path:str=None,
                 user_dir:str=None,
                 websocket_addr:str=None
        ):
        """
        Initialize the CFSolver with the specified parameters.

        Args:
            browser_type (str, optional): The type of browser to use for solving Cloudflare challenges. Defaults to 'edge'.
            proxy (str, optional): Proxy server to use for browser requests. Defaults to None.
            timeout (int, optional): Maximum time in seconds to wait for Cloudflare to resolve. Defaults to 30.
            hide_browser (bool, optional): Whether to hide the browser window during solving. Defaults to False.
            binary_path (str, optional): Path to the browser binary. Defaults to None.
            user_dir (str, optional): Path to the browser user data directory. Defaults to None.
            websocket_addr (str, optional): WebSocket address for connecting to an existing browser. Defaults to None.
        """
        self.proxy = proxy
        self.timeout = timeout
        self.browser = None
        self.browser_type = (browser_type or "edge").lower()
        self.binary_path = binary_path
        self.user_dir = user_dir if user_dir else tempfile.mkdtemp()
        self.websocket_addr = websocket_addr
        self.options = Options()
        self.options.browser_preferences = {
            "download_restrictions": 3,
            'download': {'prompt_for_download': True,'directory_upgrade': True,'extensions_to_open': '',"folderList":2 },
            'profile': {'default_content_setting_values': { 'notifications': 2, 'geolocation': 2,'media_stream_camera': 2,'media_stream_mic': 2,'popups': 1},'password_manager_enabled': False,'exit_type': 'Normal' },
            'intl': {'accept_languages': 'en-US,en','charset_default': 'UTF-8'},
            'browser': {'check_default_browser': False,'show_update_promotion_infobar': False}
        }
        
        self.options.headless = hide_browser
        if self.binary_path:
            self.options.binary_location = self.binary_path
        self._setup_options()
    
    def _setup_options(self):
        """
        Configure Chromium launch options such as user data dir, window size,
        scrollbars, resizing, and proxy.
        """
        
        self.options.add_argument(f"--user-data-dir={self.user_dir}")
        self.options.add_argument("--window-size=800,600")
        if self.proxy:
            self.options.add_argument(f"--proxy-server={self.proxy}")

    def _register_cleanup_hooks(self):
        """
        Register cleanup hooks:
        - Signal handlers (Ctrl+C, kill).
        - atexit for normal interpreter shutdown.
        - Background watchdog to kill browser if parent exits.
        """

        def handler(signum, frame):
            asyncio.get_event_loop().create_task(self._cleanup_and_exit())

        # Handle signals
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

        # Handle interpreter exit
        atexit.register(lambda: asyncio.run(self._cleanup()))

        # Watchdog (runs in background)
        asyncio.create_task(self._watch_parent_and_cleanup(os.getpid()))

    async def _watch_parent_and_cleanup(self, parent_pid):
        """Background task that kills the browser if the parent process dies."""
        try:
            proc = psutil.Process(parent_pid)
            while True:
                try:
                    # Check if parent process is still running
                    if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE:
                        if Config.LoggerV:
                            Config.logger.debug("Parent process died, cleaning up browser")
                        await self._cleanup()
                        break

                    # Also check if parent's parent (terminal/shell) is gone
                    try:
                        parent_of_parent = proc.parent()
                        if parent_of_parent and not parent_of_parent.is_running():
                            if Config.LoggerV:
                                Config.logger.debug("Parent's parent (terminal) died, cleaning up browser")
                            await self._cleanup()
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Parent's parent might not be accessible, that's okay
                        pass

                except psutil.NoSuchProcess:
                    # Parent process already died
                    if Config.LoggerV:
                        Config.logger.debug("Parent process no longer exists, cleaning up browser")
                    await self._cleanup()
                    break

                await asyncio.sleep(1)  # Check more frequently
        except Exception as e:
            if Config.LoggerV:
                Config.logger.debug(f"Error in parent watcher: {e}")

    async def _cleanup(self):
        """Close browser gracefully if running."""
        if self.browser:
            try:
                # Get the main browser process
                main_process = self.browser._browser_process_manager._process

                # Kill the main process and all its children
                try:
                    parent = psutil.Process(main_process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass

                # Also try the pydoll methods as backup
                try:
                    await main_process.terminate()
                    await main_process.kill()
                except Exception:
                    pass

            except Exception as e:
                # If pydoll methods fail, try direct process killing
                try:
                    if hasattr(self, 'browser_pid') and self.browser_pid:
                        try:
                            process = psutil.Process(self.browser_pid)
                            children = process.children(recursive=True)
                            for child in children:
                                child.kill()
                            process.kill()
                        except psutil.NoSuchProcess:
                            pass
                except Exception:
                    pass
            finally:
                self.browser = None

    async def _cleanup_and_exit(self):
        """Close browser then exit process."""
        await self._cleanup()
        sys.exit(0)

    async def _solve_once(self, url: str):
        """
        Attempt to solve Cloudflare once for a given URL.

        Args:
            url (str): The target website URL.

        Returns:
            tuple[str, str]: The Cloudflare clearance token and User-Agent string.

        Raises:
            TimeoutError: If clearance token is not found within the timeout.
        """
        self.options.add_argument(f"--app={url}")
        browser = Chrome if self.browser_type in ["chromium","chrome"] else Edge
        self.browser = browser(options=self.options)
        if self.websocket_addr:
            tab = await self.browser.connect(self.websocket_addr)
        else:
            tab = await self.browser.start()
        
        self._register_cleanup_hooks()
        await tab.go_to(url)

        start = asyncio.get_event_loop().time()
        while True:
            _token = None
            cookies = await tab.get_cookies()
            for cookie in cookies:
                if cookie["name"] == "cf_clearance":
                    _token = cookie["value"]
                    break
            if _token:
                user_agent = await tab.execute_script("return navigator.userAgent;")
                await tab.close()
                return _token, user_agent["result"]["result"]["value"]

            if asyncio.get_event_loop().time() - start > self.timeout:
                await tab.close()
                raise TimeoutError("Cloudflare cookie not found within timeout.")

            await asyncio.sleep(1)

    async def _solve(self, url: str):
        """
        Wrapper for `_solve_once` to run as a coroutine.

        Args:
            url (str): The target website URL.

        Returns:
            tuple[str, str]: Clearance token and User-Agent.
        """
        return await asyncio.create_task(self._solve_once(url))

    def solve(self, url: str):
        """
        Solve Cloudflare synchronously (blocking method).

        Args:
            url (str): The target website URL.

        Returns:
            tuple[str, str]: Clearance token and User-Agent.
        """
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self._solve_once(url))
        except RuntimeError:
            return asyncio.run(self._solve_once(url))

    def close_browser(self):
        """Synchronously close the browser with aggressive cleanup."""
        if self.browser:
            try:
                # Get the main browser process
                main_process = self.browser._browser_process_manager._process

                # Kill the main process and all its children immediately
                try:
                    parent = psutil.Process(main_process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass

                # Also try the pydoll methods as backup
                try:
                    main_process.terminate()
                    main_process.kill()
                except Exception:
                    pass

            except Exception as e:
                # If pydoll methods fail, try direct process killing
                try:
                    if hasattr(self, 'browser_pid') and self.browser_pid:
                        try:
                            process = psutil.Process(self.browser_pid)
                            children = process.children(recursive=True)
                            for child in children:
                                child.kill()
                            process.kill()
                        except psutil.NoSuchProcess:
                            pass
                except Exception:
                    pass
            finally:
                self.browser = None

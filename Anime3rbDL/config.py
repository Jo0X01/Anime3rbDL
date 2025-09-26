import sys
import signal
import atexit
from Anime3rbDL.enums import (
    EpisodeEnum,
    LastAddedEpisodesResutlsEnum,
    LatestAddedAnimeResultsEnum,
    ResolutionURLs,
    SearchResultEnum,
    TargetAnimeEnum,
    TotalSizeEnum,
    VideoObjectEnum,
    TinySearchResultEnum,
)
from fake_useragent import UserAgent


class NullLogger:
    """
    A dummy logger that discards all log messages.

    This class provides a null object pattern implementation for logging,
    allowing the application to make logging calls without checking if
    logging is enabled. Any attribute accessed will return a no-op function,
    so that logging calls will silently do nothing without raising errors.

    This is particularly useful during initialization phases or when logging
    is disabled, preventing AttributeError exceptions when logging methods
    are called before the logger is properly configured.

    The null logger supports all standard logging methods (debug, info, warning,
    error, critical, exception, log) and will silently ignore all calls,
    returning None for any operation.

    Example:
        >>> logger = NullLogger()
        >>> logger.info("This message will be silently ignored")
        >>> logger.debug("Debug info is also ignored")
        >>> logger.error("Even errors are ignored")
    """

    def __getattr__(self, name):
        """
        Return a no-op function for any attribute access.

        This method implements the null object pattern by intercepting all
        attribute access attempts and returning a no-op function that silently
        ignores any arguments passed to it.

        Args:
            name (str): The name of the attribute being accessed.
                This can be any string, including standard logging method names
                like 'info', 'debug', 'error', etc.

        Returns:
            callable: A no-op function that accepts any number of positional
                and keyword arguments and returns None. This allows the null
                logger to be used as a drop-in replacement for any logger
                without raising AttributeError exceptions.
        """
        def _noop(*args, **kwargs):
            return None

        return _noop


class _Config:
    """
    Global configuration manager for Anime3rbDL.

    This class manages all configuration settings for the Anime3rbDL application,
    including logging, network settings, download parameters, and authentication
    credentials. It provides centralized access to all configuration options.

    Attributes:
        logger (object): Logging instance (default is NullLogger).
            The active logger instance used throughout the application.
        LogFile (str): Path to log file.
            File path where logs should be written. If None, logs go to stdout.
        LoggerV (bool): Enable verbose logging if True.
            Controls whether debug-level logging is enabled.
        DownloadChunks (int): Size of chunks for downloading.
            Size in bytes for each chunk when downloading files (default: 65536).
        DownloadParts (list): Segments of a download (used internally).
            Internal list tracking download segments for resume functionality.
        WebsiteURL (str): Base website URL.
            The main URL of the anime website being scraped.
        TitleURL (str): URL for anime titles.
            URL pattern for accessing anime title pages.
        EpisodeURL (str): URL for episodes.
            URL pattern for accessing individual episodes.
        ListURL (str): URL for listing titles.
            URL for the main titles listing page.
        SearchURL (str): URL for search page.
            URL for the search functionality.
        SearchAPI (str): Endpoint for search API.
            API endpoint used for search operations.
        LoginAPI (str): Endpoint for login.
            API endpoint for user authentication.
        RegisterAPI (str): Endpoint for registration.
            API endpoint for user registration.
        DefaultResoultion (dict): Mapping of resolution names to quality labels.
            Dictionary mapping resolution keys to quality descriptions.
        CloudFlareToken (str): Token for bypassing Cloudflare.
            Pre-obtained Cloudflare clearance token to bypass protection.
        UserAgent (str): Default user agent string.
            Browser user agent string used for HTTP requests.
        HTTPProxy (dict): Proxy configuration.
            Proxy settings for HTTP/HTTPS requests (format: {"http": proxy_url, "https": proxy_url}).
        timeout (int): Default timeout for HTTP requests.
            Timeout in seconds for network requests (default: 30).
        MAX_RESULT (int): Maximum number of results allowed.
            Maximum number of search results to retrieve (default: 100).
        SolveWay (str): Method of solving captchas/challenges.
            Method for handling Cloudflare challenges ("ask", "auto", or "ignore").
        Username (str): User login name.
            Username for authentication.
        Password (str): User login password.
            Password for authentication.
        Email (str): User email address.
            Email address for authentication.
        downloader_class: Reference to the downloader class.
            Internal reference to the active downloader implementation.
        MaxWorkers (int): Maximum concurrent download workers.
            Number of parallel download threads (default: 4).
        WebsocketAddr (str): WebSocket address for browser connection.
            Address for connecting to an existing browser instance.
        hide_browser (bool): Whether to hide browser window.
            Controls browser window visibility during Cloudflare solving.
        browser_binary_path (str): Path to browser executable.
            Custom path to browser binary (Chrome, Edge, etc.).
        browser_user_dir (str): Browser user data directory.
            Custom directory for browser user data and profile.
    """

    # Logger config
    logger = NullLogger()
    LogFile: str = None
    LoggerV: bool = False
    LoggerLevel: str = "INFO"
    no_warn: bool = False
    no_color: bool = False
    SampleTestFileChunk = 1024
    MaxWorkers = 4
    DownloadChunks = 8192 * 8
    WebsocketAddr = None
    hide_browser = None
    browser_binary_path = None
    browser_user_dir = None
    DownloadParts = []
    WebsiteURL = "https://anime3rb.com/"
    TitleURL = f"{WebsiteURL}titles/"
    EpisodeURL = f"{WebsiteURL}episode/"
    ListURL = f"{TitleURL}/list"
    SearchURL = f"{WebsiteURL}search"
    SearchAPI = f"{WebsiteURL}livewire/update"
    LoginAPI = f"{WebsiteURL}login"
    RegisterAPI = f"{WebsiteURL}register"
    DefaultResoultion = {"low": "480p", "mid": "720p", "high": "1080p"}
    CloudFlareToken: str = "None"
    UserAgent: str = UserAgent().chrome
    HTTPProxy: dict = None
    timeout: int = 30
    MAX_RESULT: int = 100
    SolveWay: str = "ask"
    Username: str = None
    Password: str = None
    EpisodeTranslator: str = "default"
    Email: str = None

    @staticmethod
    def setup_logger():
        """
        Configure the logging system with enhanced verbose support.

        This method initializes the custom Anime3rbLogger with appropriate
        configuration based on the current settings. It sets up:

        - Console logging with appropriate level (DEBUG if verbose enabled, else INFO)
        - File logging if a log file path is specified
        - Enhanced formatting with timestamps, colors, and contextual information
        - Support for verbose mode with detailed debug information

        The method updates the `Config.logger` reference with the active logger
        instance and registers cleanup handlers for proper resource management.

        Raises:
            Exception: If logger configuration fails, but continues execution
                      with fallback logging.
        """
        try:
            from Anime3rbDL.logger import get_logger
            Config.logger = get_logger(
                verbose=Config.LoggerV,
                log_file=Config.LogFile,
                level=Config.LoggerLevel
            )
        except Exception as e:
            # Fallback to NullLogger if setup fails
            print(f"Logger setup failed: {e}", file=sys.stderr)
            Config.logger = NullLogger()

        # Register cleanup handlers for proper browser cleanup on exit
        Config._register_cleanup_handlers()

    @staticmethod
    def _register_cleanup_handlers():
        """
        Register cleanup handlers for various exit scenarios.

        This method sets up comprehensive cleanup handlers to ensure proper
        resource management and browser cleanup in all exit scenarios:

        - Application exits normally (atexit handler)
        - User presses Ctrl+C (SIGINT signal handler)
        - Application is terminated (SIGTERM signal handler)
        - Python interpreter shuts down (atexit handler)

        The handlers perform the following cleanup operations:
        - Close any open browser instances used for Cloudflare solving
        - Clean up orphaned browser processes that might remain
        - Log cleanup operations in verbose mode
        - Ensure proper exit codes are maintained

        Note:
            This method starts a background thread that periodically cleans
            up orphaned browser processes to prevent resource leaks.
        """
        def cleanup_handler():
            """Handler that performs cleanup before exit."""
            try:
                from Anime3rbDL.client import Anime3rbHTTPClient
                Anime3rbHTTPClient.close_browser()
            except Exception:
                pass  # Ignore cleanup errors during signal handling

        # Register cleanup for normal exit
        atexit.register(cleanup_handler)

        # Register cleanup for signals (Ctrl+C, kill, etc.)
        def signal_handler(signum, frame):
            """Handle signals by cleaning up and exiting."""
            if Config.LoggerV:
                Config.logger.debug(f"Received signal {signum}, performing aggressive cleanup...")

            # Perform immediate cleanup
            cleanup_handler()

            # Also try to clean up any remaining browser processes that might be related
            try:
                from Anime3rbDL.client import Anime3rbHTTPClient
                Anime3rbHTTPClient.cleanup_orphaned_browsers()
            except Exception:
                pass

            if Config.LoggerV:
                Config.logger.debug("Cleanup complete, exiting...")

            # Exit immediately with standard signal exit codes
            sys.exit(128 + signum)

        # Start a background task to periodically clean up orphaned browsers
        def start_orphan_cleanup_task():
            """Start a background task to clean up orphaned browsers."""
            import threading
            import time

            def orphan_cleanup_worker():
                """Background worker that cleans up orphaned browsers."""
                while True:
                    try:
                        from Anime3rbDL.client import Anime3rbHTTPClient
                        Anime3rbHTTPClient.cleanup_orphaned_browsers()
                    except Exception:
                        pass  # Ignore errors in background task
                    time.sleep(5)  # Check every 5 seconds

            # Start the background thread
            cleanup_thread = threading.Thread(target=orphan_cleanup_worker, daemon=True)
            cleanup_thread.start()

        # Start the orphan cleanup task
        start_orphan_cleanup_task()

        # Set signal handlers - these will override any existing ones
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    @staticmethod
    def exit(status_code: int|str = 0):
        """
        Exit the application with the provided status code and cleanup resources.

        This method provides a centralized exit mechanism that ensures proper
        cleanup of all resources before terminating the application. It performs
        the following operations:

        - Closes any open browser instances used for Cloudflare solving
        - Cleans up temporary files and connections
        - Logs the exit operation in verbose mode
        - Handles cleanup errors gracefully without affecting exit status
        - Terminates the application with the specified exit code

        This method should be used instead of sys.exit() throughout the
        application to ensure consistent cleanup behavior.

        Args:
            status_code (int|str): Exit code to return to the operating system.
                0 indicates successful execution, non-zero indicates an error.
                Can be an integer or string message. Defaults to 0.

        Note:
            This method will attempt to import and use Anime3rbHTTPClient
            for browser cleanup. If the import fails, it will continue
            with normal exit behavior.
        """
        try:
            # Import here to avoid circular imports
            from Anime3rbDL.client import Anime3rbHTTPClient

            # Close any open browser instances
            if Config.LoggerV:
                Config.logger.debug("Performing application cleanup during exit")

            Anime3rbHTTPClient.close_browser()

            if Config.LoggerV:
                Config.logger.debug(f"Application exiting with status code: {status_code}")

        except ImportError:
            # If import fails, just continue with normal exit
            if Config.LoggerV:
                Config.logger.debug("Could not import HTTP client for cleanup")
        except Exception as e:
            if Config.LoggerV:
                Config.logger.debug(f"Error during exit cleanup: {e}")
            # Continue with exit even if cleanup fails

        sys.exit(status_code)

class _Cache:
    """
    Global cache to hold runtime data for Anime3rbDL.

    This class serves as a centralized storage for runtime data that needs to be
    shared across different components of the Anime3rbDL application. It maintains
    state information about the current anime being processed, search results,
    download information, and user inputs.

    The cache is designed to be thread-safe for concurrent operations and provides
    a single source of truth for the application's runtime state. All attributes
    are class-level variables that persist throughout the application's lifecycle.

    Attributes:
        ANIME_URL (str): Currently processed anime URL.
            The URL of the anime currently being processed or downloaded.
            Set during search operations and used throughout the download process.
        TARGET_EPISODE_ANIME (VideoObjectEnum): Current episode object.
            The specific episode object being processed, containing episode metadata
            and video information. Used for individual episode operations.
        TARGET_TVSeries_ANIME (TargetAnimeEnum): Current TV series object.
            The main anime/series object containing overall series information,
            including title, description, and episode count.
        TotalSize (TotalSizeEnum): Size summary of available resolutions.
            Contains calculated total sizes for all available resolutions (low, mid, high)
            to help users understand download requirements before starting.
        DownloadInfo (ResolutionURLs): Resolution and download data.
            Contains detailed download URLs and metadata for each available resolution,
            organized by quality level.
        SearchResult (SearchResultEnum): Results from a full search query.
            Complete search results from detailed search operations, containing
            comprehensive anime information and metadata.
        TinySearchResult (TinySearchResultEnum): Results from a lightweight search query.
            Lightweight search results for quick operations, containing essential
            information without full metadata.
        USER_INPUT_URL (str): Original user input URL.
            The original URL or search query provided by the user, preserved
            for reference and logging purposes.
        ANIME_TITLE (str): Title of the anime being processed.
            The human-readable title of the current anime, extracted from
            the anime page or search results.
        ANIME_QUERY_SEARCH (str): Query string used for searching.
            The search query string used to find the current anime, useful
            for logging and debugging purposes.
        ANIME_SEARCH_URL (str): URL used for anime search.
            The specific search URL used to locate the current anime,
            which may differ from the final anime page URL.
        EpisodesDownloadData (list[EpisodeEnum]): List of episodes prepared for download.
            A curated list of episode objects that have been selected for download,
            containing all necessary information for the download process.
    """

    ANIME_URL: str = None
    TARGET_EPISODE_ANIME: VideoObjectEnum = VideoObjectEnum()
    TARGET_TVSeries_ANIME: TargetAnimeEnum = TargetAnimeEnum()
    LastAddedAnimes:LatestAddedAnimeResultsEnum = None
    LastAddedEpisodes:LastAddedEpisodesResutlsEnum = None
    TotalSize = TotalSizeEnum()
    DownloadInfo = ResolutionURLs()
    SearchResult: SearchResultEnum = SearchResultEnum()
    TinySearchResult: TinySearchResultEnum = TinySearchResultEnum()
    USER_INPUT_URL: str = None
    ANIME_TITLE: str = None
    ANIME_QUERY_SEARCH: str = None
    ANIME_SEARCH_URL: str = None
    EpisodesDownloadData: list[EpisodeEnum] = []


# Global instances
Cache = _Cache()
Config = _Config()

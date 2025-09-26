from typing import Union
from Anime3rbDL.enums import AppTypes, CustomTypes, SearchResultEnum, TargetAnimeEnum, TinySearchResultEnum, VideoObjectEnum
from Anime3rbDL.parser import ParserUtils, Cache, Config
from Anime3rbDL.client import Anime3rbHTTPClient
import os

class Anime3rbDL:
    """Main class for handling anime search, login, registration, information retrieval,
    and downloading from Anime3rb.

    This class provides a high-level interface for interacting with the Anime3rb website,
    including authentication, searching for anime, fetching episode information, and
    downloading content. It integrates with the parser, client, and downloader modules
    to provide a seamless experience.

    Attributes:
        None (stateless class using global Config and Cache).
    """

    def __init__(self, enable_logger: bool = True, verbose: bool = False, log_file: str = None):
        """Initialize the Anime3rbDL downloader instance.

        Sets up logging configuration and prepares the application for use. Logging
        is configured globally via the Config module.

        Args:
            enable_logger (bool, optional): Whether to enable logging output.
                If False, all logging is disabled. Defaults to True.
            verbose (bool, optional): Enable verbose/debug logging with detailed
                information and full tracebacks. Defaults to False.
            log_file (str, optional): Path to a file where logs should be saved.
                If None, logs are only output to stdout/stderr. Defaults to None.
        """
        if enable_logger:
            Config.LoggerV = verbose
            Config.LogFile = os.path.normpath(log_file) if log_file and log_file.strip() else None
            Config.setup_logger()

            if verbose:
                Config.logger.debug("Anime3rbDL initialized with verbose logging enabled")
                Config.logger.debug(f"Log file configured: {log_file}")
            else:
                Config.logger.info("Anime3rbDL initialized successfully")
        
        
    def login(self, email: str, password: str) -> bool:
        """Log in to Anime3rb with user credentials.

        Attempts to authenticate the user with the provided email and password.
        Updates the global Config with credentials and calls the parser to handle login.

        Args:
            email (str): User's email address for login.
            password (str): User's password for login.

        Returns:
            bool: True if login was successful, False otherwise.

        Side Effects:
            - Updates Config.Email and Config.Password.
            - Logs success or failure messages.
        """
        Config.Email = email
        Config.Password = password
        success = ParserUtils.parse_login_page()
        if Config.LoggerV:
            Config.logger.debug(f"Login attempt for {email}: {'successful' if success else 'failed'}")
        return success
        
    def register(self, username: str, email: str, password: str) -> bool:
        """Register a new Anime3rb account.

        Attempts to create a new user account with the provided details.
        Updates the global Config with credentials and calls the parser to handle registration.

        Args:
            username (str): Desired username for the new account.
            email (str): Email address for the new account.
            password (str): Password for the new account.

        Returns:
            bool: True if registration was successful, False otherwise.

        Side Effects:
            - Updates Config.Username, Config.Email, and Config.Password.
            - Logs success or failure messages.
        """
        Config.Username = username
        Config.Password = password
        Config.Email = email
        success = ParserUtils.parse_register_page()
        if Config.LoggerV:
            Config.logger.debug(f"Registration attempt for {username} ({email}): {'successful' if success else 'failed'}")
        return success
    
    def search(
        self,
        query: str = None,
        index: int = None,
        max_results: int = None,
        fast_mode: bool = True
    ):
        """Search for anime based on a query or URL. If no query is provided, fetch the latest anime releases.

        Args:
            query (str, optional):
                Either an anime page URL or a search query string. If None, fetch latest releases.
            index (int, optional):
                Pick search result by index. Defaults to None.
            max_results (int, optional):
                Maximum number of results to return. Defaults to `Config.MAX_RESULT`.
            fast_mode (bool, optional):
                Use a faster but less detailed search method. Defaults to True.

        Returns:
            Union[LatestAddedAnimeResultsEnum, LastAddedEpisodesResutlsEnum, TinySearchResultEnum, SearchResultEnum, VideoObjectEnum, TargetAnimeEnum, list]:
                - Parsed anime data if query is a direct URL.
                - Parsed anime data if search returns exactly one result (auto-selected).
                - Search results object if search returns multiple results.
                - tuple of latest anime releases if query is None.
        """
        if query is None:
            # Fetch latest anime releases
            return self.get_latest(max_results or 30)

        if max_results:
            Config.MAX_RESULT = max_results

        if Config.LoggerV:
            Config.logger.debug(f"Searching for query: '{query}'")
            Config.logger.debug(f"Search parameters - Index: {index}, Max results: {max_results}, Fast mode: {fast_mode}")

        if ParserUtils.parse_query(query):
            if Config.LoggerV:
                Config.logger.debug("Query detected as direct URL, parsing title page")
            return ParserUtils.parse_title_page()
        if Config.LoggerV:
            Config.logger.debug(f"Query detected as search term, using {'tiny' if fast_mode else 'full'} search")

        results = ParserUtils.parse_tiny_search_page() if fast_mode else ParserUtils.parse_search_page()

        # If only one result found, automatically select it
        if results.Count == 1:
            if Config.LoggerV:
                Config.logger.debug("Only one search result found, automatically selecting it")
            single_result = results.getByVal(0)
            if Config.LoggerV:
                Config.logger.debug(f"Auto-selected: {single_result.Title}")
            return self.search(single_result.url)

        if index is not None:
            if Config.LoggerV:
                Config.logger.debug(f"Selecting result by index: {index}")
            try:
                return self.search(results.getByVal(index-1).url)
            except IndexError:
                if Config.LoggerV:
                    Config.logger.debug(f"Index {index} out of range for search results")
                raise ValueError(f"Index {index} is out of range for the search results.")
        return results
    
    def get_latest(self, max_fetch: int = 30):
        """Fetch the latest anime releases from the website.

        This method retrieves the most recent anime additions and episodes by parsing
        the main page and following pagination links. It populates the cache with
        latest anime and episode data, associating episodes with their respective anime.

        Args:
            max_fetch (int, optional):
                Maximum number of latest releases to retrieve. Defaults to 30.

        Returns:
            tuple: A tuple containing the latest anime results and episode results.
                   (LatestAddedAnimeResultsEnum, LastAddedEpisodesResutlsEnum)

        Side Effects:
            - Updates Cache.LastAddedAnimes and Cache.LastAddedEpisodes.
            - Logs the fetching process and any errors.
        """
        
        if max_fetch:
            Config.MAX_RESULT = max_fetch
        return ParserUtils.parse_get_latest()

    def get_info(
        self,
        download_parts: str = "all",
        res: str = "low",
        download: bool = False,
        path: str = "."
    ):
        """Retrieve detailed information about anime episodes and optionally download them.

        Parses episode data for the currently selected anime, filtering by specified parts
        and resolution. Can either return episode information or immediately download files.

        Args:
            download_parts (str): Episodes to fetch, e.g., "all", "1-3,5", "latest". Defaults to "all".
            res (str): Resolution to prepare ("low", "mid", "high"). Defaults to "low".
            download (bool): If True, start downloading immediately after gathering info. Defaults to False.
            path (str): Destination folder for downloads (used only if download=True). Defaults to ".".

        Returns:
            list:
                - If download=False: List of `EpisodeEnum` objects with resolution info.
                - If download=True: List of file paths of downloaded episodes.

        Side Effects:
            - Updates Cache.EpisodesDownloadData with episode information.
            - Creates output directory if downloading.
            - Logs parsing and download progress.
        """
        if Config.LoggerV:
            Config.logger.debug(f"Gathering episode info - Parts: {download_parts}, Resolution: {res}, Download: {download}, Path: {path}")

        ParserUtils.parse_skip_parts(download_parts)

        if not download:
            if Config.LoggerV:
                Config.logger.debug("Retrieving episode information without downloading")
            episodes = ParserUtils.parse_episodes_info(res)
            if Config.LoggerV:
                Config.logger.debug(f"Retrieved info for {len(episodes)} episodes")
            return episodes

        if Config.LoggerV:
            Config.logger.debug("Retrieving episode info with immediate download")

        downloaded_files = []
        episode_count = 0

        for episode in ParserUtils.yield_episodes_info(res):
            episode_count += 1
            if type(episode) == AppTypes.IsEpisode:
                episode = episode.Video
            output_dir = f"{path}/{Cache.ANIME_TITLE}/"
            file_path = Anime3rbHTTPClient.download_file(
                episode.DownloadData.getByVal(res),
                output_dir
            )
            downloaded_files.append(file_path)
            if Config.LoggerV:
                Config.logger.debug(f"Downloaded episode {episode_count}: {file_path}")

        if Config.LoggerV:
            Config.logger.debug(f"Completed downloading {len(downloaded_files)} episodes")
        return downloaded_files

    def download(self, path: str = ".", res: str = "low") -> list:
        """Download all episodes in Cache.EpisodesDownloadData to the specified directory.

        Downloads all episodes that have been prepared via get_info(). Creates an output
        directory based on the anime title and downloads each episode sequentially.

        Args:
            path (str, optional): Destination folder. Defaults to current directory.
            res (str, optional): Resolution to download ("low", "mid", "high"). Defaults to "low".

        Returns:
            list: List of file paths for successfully downloaded episodes.

        Notes:
            - Uses Downloader class for actual downloading.
            - Handles episodes stored either as EpisodeEnum or VideoObjectEnum.
            - Requires get_info() to be called first to populate episode data.
            - Prints progress to console and logs detailed information.

        Raises:
            RuntimeError: If get_info() has not been called before download().

        Side Effects:
            - Creates output directory if it doesn't exist.
            - Updates console output with download progress.
            - Logs download status and file paths.
        """

        # Check if get_info() has been called first
        if not Cache.EpisodesDownloadData:
            error_msg = (
                "No episode data available for download. "
                "Please call get_info() first to gather episode information. "
                "Example: anime.get_info('all', 'low')"
            )
            if Config.LoggerV:
                Config.logger.error(error_msg)
            raise RuntimeError(error_msg)

        output_dir = os.path.join(path, Cache.ANIME_TITLE)
        total_eps = len(Cache.EpisodesDownloadData)

        if Config.LoggerV:
            Config.logger.debug(f"Starting download - Path: {output_dir}, Resolution: {res}, Total episodes: {total_eps}")

        downloaded_files = []
        for idx, episode in enumerate(Cache.EpisodesDownloadData, 1):
            if Config.LoggerV:
                Config.logger.debug(f"Downloading episode {idx}/{total_eps}")
            print(f"Downloading episode {idx}/{total_eps}")
            if type(episode) == AppTypes.IsEpisode:
                episode = episode.Video
            try:
                file_path = Anime3rbHTTPClient.download_file(
                    episode.DownloadData.getByVal(res),
                    output_dir
                )
                downloaded_files.append(file_path)
                if Config.LoggerV:
                    Config.logger.debug(f"Successfully downloaded episode {idx}: {file_path}")
            except Exception as e:
                if Config.LoggerV:
                    Config.logger.debug(f"Failed to download episode {idx}: {e}")
                print(f"Failed to download episode {idx}: {e}")
        return downloaded_files

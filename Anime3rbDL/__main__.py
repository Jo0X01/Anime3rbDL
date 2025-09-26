#!/usr/bin/env python3
import sys
import traceback
import warnings
from typing import Optional

import click
from rich.console import Console

from Anime3rbDL import Anime3rbDL, Cache, Config
from Anime3rbDL.enums import AppTypes

# Global flag for suppressing warnings
_suppress_warnings = False

def no_warn_callback(ctx, param, value):
    """Callback for --no-warn option to suppress warnings early."""
    if value:
        import warnings
        warnings.filterwarnings('ignore')
        global _suppress_warnings
        _suppress_warnings = True
        Config.no_warn = True
    return value

console = Console()

LOGO = r"""
    ___          _               _____      __    ____  __
   /   |  ____  (_)___ ___  ___ |__  /_____/ /_  / __ \/ /
  / /| | / __ \/ / __ `__ \/ _ \ /_ </ ___/ __ \/ / / / /
 / ___ |/ / / / / / / / / /  __/__/ / /  / /_/ / /_/ / /___
/_/  |_/_/ /_/_/_/ /_/ /_/\___/____/_/  /_.___/_____/_____

    [+] Anime3rbDL - Download Anime Easily!
    [+] By: MrJo0x01 | Discord: mr_jo0x01

"""





def handle_auth(anime: Anime3rbDL, login: Optional[tuple[str, str]], register: Optional[tuple[str, str, str]]) -> None:
    """Handles user authentication (login or registration) based on CLI arguments.

    Processes login or registration credentials from arguments and invokes the
    corresponding Anime3rbDL methods. Logs authentication attempts and outcomes.

    Args:
        anime (Anime3rbDL): Initialized Anime3rbDL instance for authentication.
        login (Optional[tuple[str, str]]): Login credentials (email, password).
        register (Optional[tuple[str, str, str]]): Registration credentials (username, email, password).

    Side Effects:
        - Performs login or registration via the anime instance.
        - Logs success/failure of auth operations if verbose mode is enabled.
    """
    if login:
        email, password = login
        if Config.LoggerV:
            Config.logger.debug(f"Attempting login for email: {email}")
        success = anime.login(email, password)
        if Config.LoggerV:
            Config.logger.debug(f"Login result for {email}: {'success' if success else 'failed'}")
        if not success:
            Config.logger.warning("Login failed. Some features may be unavailable.")
    if register:
        username, email, password = register
        if Config.LoggerV:
            Config.logger.debug(f"Attempting registration for username: {username}, email: {email}")
        success = anime.register(username, email, password)
        if Config.LoggerV:
            Config.logger.debug(f"Registration result for {username}: {'success' if success else 'failed'}")
        if not success:
            Config.logger.warning("Registration failed. Please check credentials and try again.")


def handle_search(anime: Anime3rbDL, query: Optional[str], latest: bool, deep_search: bool, search_index: Optional[int], max_results: Optional[int], download_parts: Optional[str], verbose: bool) -> tuple[str, Optional[str]]:
    """Handles anime search or latest releases retrieval and user selection.

    Determines if latest releases or a specific query search is needed. For latest,
    fetches and displays anime/episode lists. For queries, performs search (tiny or full),
    handles multiple results by displaying options and user input, and selects the target
    anime URL. Also prompts for download parts if multiple episodes.

    Args:
        anime (Anime3rbDL): Initialized Anime3rbDL instance for searching.
        query (Optional[str]): Search query or URL.
        latest (bool): Flag for latest releases.
        deep_search (bool): Flag for deep search.
        search_index (Optional[int]): Index of search result.
        max_results (Optional[int]): Max search results.
        download_parts (Optional[str]): Episodes to download.
        verbose (bool): Verbose logging.

    Returns:
        tuple[str, Optional[str]]: The final query and updated download_parts.

    Side Effects:
        - Fetches and logs latest releases or search results.
        - Interacts with user for selection if multiple results.
        - Updates download_parts based on user input.
        - Exits on invalid input or no results.
    """
    if latest:
        if Config.LoggerV:
            Config.logger.info("Fetching latest anime and episode releases...")
        if verbose:
            Config.logger.debug(f"Latest releases max results: {max_results or 30}")

        _anime, episodes = anime.get_latest(max_results)  # fast_mode=True for latest

        if _anime is None and episodes is None:
            Config.logger.error("No latest releases found or fetch failed")
            Config.exit("[ERR] No latest releases available at this time.")

        Config.logger.info(f"Successfully fetched {_anime.Count} latest anime releases")
        Config.logger.info(f"Successfully fetched {episodes.Count} latest episode releases")

        click.echo(f"[+] Latest Anime Releases ({_anime.Count}):")
        for _an in _anime.Results:
            click.echo(f" - [+] {_an.Name}")
            click.echo(f"     |-> Last Added: {_an.LastAddedStr}")
            click.echo(f"     |-> Rate: {_an.Rate} - Year: {_an.PublishYear} - Count: {_an.NumberOfEpisodes}")
            click.echo(f"     |-> URL: {_an.url}")
            click.echo(f"     |-> Image: {_an.BannerLink}")

        click.echo(f"[+] Latest Episodes Releases ({episodes.Count}):")
        for _an in episodes.Results:
            click.echo(f" - [+] {_an.name}")
            click.echo(f"     | {_an.Type} -> Last Added: {_an.index}")
            click.echo(f"     |-> URL: {_an.url}")
            click.echo(f"     |-> Image: {_an.image}")
        Config.exit("Latest releases displayed successfully.")

    Config.logger.info(f"Performing search for query: '{query}'")
    if verbose:
        Config.logger.debug(f"Search config - Deep search: {deep_search}, Max results: {max_results}, Index: {search_index}")

    search_mode = not deep_search  # fast_mode = True if not deep
    _found = anime.search(query, search_index, max_results, search_mode)

    if _found is None:
        Config.logger.error(f"Search returned no results for query: '{query}'")
        Config.exit(f"[ERR] No anime found matching: {query}")

    Config.logger.info("Search operation completed successfully")

    if type(_found) in [AppTypes.IsSearch, AppTypes.IsDeepSearch]:
        num_results = len(_found.Results)
        Config.logger.info(f"Search yielded {num_results} results")
        if not search_index:
            Config.logger.info("Prompting user for result selection...")
            for idx, _anime in enumerate(_found.Results, start=1):
                click.echo(f"[{idx}] {_anime.Title}")
                click.echo(f"  |-> Episodes: {_anime.NumberOfEpisodes} | Year: {_anime.PublishYear} | Rate: {_anime.Rate}")
            try:
                search_index = click.prompt("Select anime by number", type=int)
                Config.logger.info(f"User selected result index: {search_index}")
            except ValueError:
                Config.logger.error("Invalid numeric input for search index")
                Config.exit("[ERR] Please enter a valid number for selection.")
        choice = _found.getByVal(search_index - 1)
        Config.logger.info(f"User selected anime: '{choice.Title}'")
        if verbose:
            Config.logger.debug(f"Navigating to selected anime URL: {choice.url}")

        _found = anime.search(choice.url)
        
    # Display detailed anime information
    click.echo(f"\n[+] Anime Details: {_found.Type.value}")
    click.echo(f"    |-> Name: {_found.ClearTitle}")
    click.echo(f"    |-> Status: {_found.Status}")
    click.echo(f"    |-> Banner: {_found.BannerURL}")
    click.echo(f"    |-> URL: {_found.Url}")
    desc = _found.Description or 'No description available'
    if len(desc) > 200:
        desc = desc[:100] + "..."
    click.echo(f"    |-> Description: {desc}")
    click.echo(f"    |-> Publish Date: {_found.PublishDate.date()}")
    click.echo(f"    |-> Rating: {_found.Rate}/10")
    click.echo(f"    |-> Total Episodes: {_found.EpisodesCount}")
    click.echo(f"    |-> Genres: {','.join(_found.Genres)}")
    click.echo(f"    |-> Contributors: ")
    for cont in _found.Contributors:
        click.echo(f"       - [{cont.role}] {cont.name} : {cont.url}")
    click.echo(f"    |-> Trailers: ")
    for cont in _found.TrialersUrls:
        click.echo(f"       - [{cont}]")
    
    if verbose:
        Config.logger.debug(f"Displayed anime details for: {_found.Title}")
    if download_parts is None and _found.EpisodesCount > 1:
        download_parts = click.prompt(
            f"Specify episodes to download (e.g., '1-3,5,8') (Default: 1-{_found.EpisodesCount})",
            default="all",
            show_default=False
        )
        Config.logger.info(f"User-specified download parts: '{download_parts}'")

    if download_parts is None:
        download_parts = "all"
        Config.logger.debug("Default download parts set to 'all'")

    return query, download_parts


def handle_download(anime: Anime3rbDL, download_parts: str, res: Optional[str], output_dir: str, download_now: bool, verbose: bool) -> None:
    """Manages episode information retrieval and download process.

    Fetches episode details for the selected anime, displays size info for resolutions,
    and handles user confirmation for download. Supports immediate download mode without
    size preview. Logs all steps including user decisions and outcomes.

    Args:
        anime (Anime3rbDL): Anime3rbDL instance ready for info/download.
        download_parts (str): Episodes to download.
        res (Optional[str]): Resolution (low/mid/high).
        output_dir (str): Output directory.
        download_now (bool): Immediate download flag.
        verbose (bool): Verbose logging.

    Side Effects:
        - Calls get_info() to populate episode data.
        - Displays download sizes and prompts user for confirmation.
        - Initiates download if confirmed, logs progress and completion.
        - Exits on immediate download completion.
    """
    target_res = res or "low"
    Config.logger.info(f"Retrieving episode download information for resolution: {target_res}")
    if verbose:
        Config.logger.debug(f"Download setup - Parts: '{download_parts}', Output: '{output_dir}', Immediate: {download_now}")

    if download_now:
        Config.logger.info("Initiating immediate download (skipping size preview)...")
        downloaded = anime.get_info(download_parts, target_res, download=True, path=output_dir)
        Config.logger.info(f"Immediate download completed: {len(downloaded)} files saved")
        Config.exit("\n[INFO] Immediate download finished successfully!")

    episodes_info = anime.get_info(download_parts, target_res)
    Config.logger.info(f"Episode information retrieved: {len(episodes_info)} episodes prepared")

    click.echo("[+] Download Information:")
    if res:
        _, file_size = Cache.TotalSize.getByVal(res)
        click.echo(f" |---> {str(res).capitalize()} Resolution = {file_size}")
        if verbose:
            Config.logger.debug(f"Selected resolution size: {file_size}")
    else:
        click.echo(f" |---> Low Resolution  = {Cache.TotalSize.FLow}")
        click.echo(f" |---> Mid Resolution  = {Cache.TotalSize.FMid}")
        click.echo(f" |---> High Resolution = {Cache.TotalSize.FHigh}")
        if verbose:
            Config.logger.debug(f"Available sizes - Low: {Cache.TotalSize.FLow}, Mid: {Cache.TotalSize.FMid}, High: {Cache.TotalSize.FHigh}")

    if verbose:
        Config.logger.debug(f"Prepared {len(Cache.EpisodesDownloadData)} episodes for download")
        Config.logger.debug(f"Target output directory: {output_dir}")

    user_confirm = click.confirm(f"Proceed with download in [{target_res}] resolution?", default=True)
    if user_confirm:
        Config.logger.info(f"User confirmed download in {target_res} resolution to {output_dir}")
        downloaded_files = anime.download(path=output_dir, res=target_res)
        Config.logger.info(f"Download process completed: {len(downloaded_files)} episodes downloaded")
        click.echo("\n[INFO] All episodes downloaded successfully!")
    else:
        Config.logger.info("User cancelled the download operation")
        click.echo("\n[INFO] Download cancelled by user.")


@click.command()
@click.argument('query', required=False)
@click.option('-l', '--latest', is_flag=True, help="Fetch and display latest anime releases.")
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose/debug logging output.")
@click.option('-lf', '--log-file', metavar="FILE", help="Save logs to a file instead of stdout.")
@click.option('-nl', '--no-logger', is_flag=True, help="Disable logging entirely.")
@click.option('--debug', is_flag=True, help="Show full traceback on errors.")
@click.option("-nw",'--no-warn', is_flag=True, callback=no_warn_callback, help="Disable all warnings.")
@click.option("-nc",'--no-color', is_flag=True, help="Disable colored output.")
@click.option('-t', '--timeout', type=int, default=30, metavar="SECONDS", help="Request timeout (default: 30s).")
@click.option('-ct', '--cf-token', metavar="TOKEN", help="Manually provide Cloudflare token (`cf_clearance`).")
@click.option('-ua', '--user-agent', metavar="UA_STRING", help="Override default User-Agent.")
@click.option('-p', '--proxy', metavar="URL", help="Proxy server (e.g. http://127.0.0.1:8080).")
@click.option('-e', '--on-expire-token', type=click.Choice(['ask', 'auto', 'ignore']), default='ask', help="Action if Cloudflare token expires (default: ask).")
@click.option('--login', nargs=2, type=str, metavar=("EMAIL", "PASSWORD"), help="Login with email and password.")
@click.option('--register', nargs=3, type=str, metavar=("USERNAME", "EMAIL", "PASSWORD"), help="Register new account.")
@click.option('-tr', '--translator', metavar="TEXT", help="Episode translator to use [Netflix,Crunchyroll,Rocks-Team,etc...] (takes random one).")
@click.option('-ds', '--deep-search', is_flag=True, help="Use deep search mode.")
@click.option('-si', '--search-index', type=int, help="Pick search result by index.")
@click.option('-n', '--max-results', type=int, help="Maximum number of search results to show.")
@click.option('-d', '--download-parts', metavar="RANGE", help="Episodes to download (e.g. 1-3,5,8).")
@click.option('-c', '--download-chunks', metavar="CHUNKS", help="Number of chunks per download.")
@click.option('-m', '--max-workers', type=int, default=4, metavar="N", help="Max concurrent workers (default: 4).")
@click.option('-r', '--res', type=click.Choice(['low', 'mid', 'high']), default='low', help="Resolution to fetch (default: low).")
@click.option('-dn', '--download-now', is_flag=True, help="fetch info about (default resolution or u given) Then Download Without calculate total size")
@click.option('-o', '--output-dir', default=".", metavar="DIR", help="Directory to save downloads.")
@click.option("-hb",'--hide-browser', is_flag=True, help="hide browser window during Cloudflare challenge. May fail to solve sometimes.")
@click.option("-bp",'--binary-path', metavar="PATH", help="path to browser binary (Edge , Chrome, Chromium) Only.")
@click.option("-ud",'--user-dir', metavar="DIR", help="path to browser user data directory.")
@click.option("-ws",'--ws-addr', metavar="WEBSOCKET_ADDRESS", help="Connect to existing browser (Edge , Chrome, Chromium) Only via WebSocket URL.")
def main(query, latest, verbose, log_file, no_logger, debug, no_warn, no_color, timeout, cf_token, user_agent, proxy, on_expire_token, login, register, translator, deep_search, search_index, max_results, download_parts, download_chunks, max_workers, res, download_now, output_dir, hide_browser, binary_path, user_dir, ws_addr):
    """Primary entry point for the Anime3rbDL command-line application.

    Manages the full execution lifecycle: displays logo, parses CLI arguments,
    applies configurations (e.g., proxy, timeout, auth), initializes logging and
    the Anime3rbDL instance, handles authentication, executes search or latest fetch,
    and orchestrates downloads. Includes comprehensive error handling for interrupts
    and exceptions, with optional debug tracebacks.

    Handles:
        - Argument validation and help display.
        - Global config updates from CLI flags.
        - Warning suppression if requested.
        - Sequential calls to auth, search, and download handlers.
        - Graceful exits with status messages.

    Raises:
        KeyboardInterrupt: Caught and handled with user cancellation message.
        Exception: Caught, logged, and exited with error message (full traceback if --debug).

    Side Effects:
        - Prints application logo and final thank-you message.
        - Initializes and configures logging based on args.
        - Updates Config globals with parsed values.
    """
    try:
        if not latest and query is None:
            click.echo("Please provide a search query or use --latest to fetch latest releases. Use --help for more options.")
            sys.exit(1)

        # Update global configurations from CLI arguments
        Config.LoggerV = bool(verbose)
        Config.no_warn = bool(no_warn)
        Config.no_color = bool(no_color)
        if cf_token:
            Config.CloudFlareToken = cf_token
            if Config.LoggerV:
                Config.logger.debug(f"Cloudflare token set manually")
        if user_agent:
            Config.UserAgent = user_agent
            if Config.LoggerV:
                Config.logger.debug(f"User-Agent overridden: {Config.UserAgent}")
        if proxy:
            Config.HTTPProxy = proxy
            if Config.LoggerV:
                Config.logger.debug(f"Proxy configured: {Config.HTTPProxy}")
        if on_expire_token:
            Config.SolveWay = on_expire_token
            if Config.LoggerV:
                Config.logger.debug(f"Token expiration handling: {Config.SolveWay}")
        if max_results:
            Config.MAX_RESULT = max_results
            if Config.LoggerV:
                Config.logger.debug(f"Max search results set to: {Config.MAX_RESULT}")
        if download_chunks:
            Config.DownloadChunks = int(download_chunks)
            if Config.LoggerV:
                Config.logger.debug(f"Download chunks set to: {Config.DownloadChunks}")
        if max_workers:
            Config.MaxWorkers = int(max_workers)
            if Config.LoggerV:
                Config.logger.debug(f"Max workers set to: {Config.MaxWorkers}")
        if ws_addr:
            Config.WebsocketAddr = ws_addr
            if Config.LoggerV:
                Config.logger.debug(f"WebSocket address: {Config.WebsocketAddr}")
        if hide_browser:
            Config.hide_browser = hide_browser
            if Config.LoggerV:
                Config.logger.debug("Browser window hidden enabled")
        if binary_path:
            Config.browser_binary_path = binary_path
            if Config.LoggerV:
                Config.logger.debug(f"Browser binary path: {Config.browser_binary_path}")
        if user_dir:
            Config.browser_user_dir = user_dir
            if Config.LoggerV:
                Config.logger.debug(f"Browser user data dir: {Config.browser_user_dir}")
        if timeout:
            if timeout <= 0:
                Config.exit("[ERR] Request timeout must be greater than 0 seconds")
            Config.timeout = int(timeout)
            if Config.LoggerV:
                Config.logger.debug(f"Request timeout set to: {Config.timeout}s")
        if translator:
            Config.EpisodeTranslator = translator
            if Config.LoggerV:
                Config.logger.debug(f"Episode translator set to: {Config.EpisodeTranslator}")

        # Initialize application and logging
        Config.logger.info("Starting Anime3rbDL application initialization...")
        anime = Anime3rbDL(not no_logger, verbose, log_file)
        Config.logger.info("Anime3rbDL instance initialized successfully")

        if verbose:
            Config.logger.debug("Active configuration summary:")
            Config.logger.debug(f"  - Cloudflare handling: '{Config.SolveWay}'")
            Config.logger.debug(f"  - User-Agent: '{Config.UserAgent}'")
            Config.logger.debug(f"  - Request timeout: {Config.timeout}s")
            Config.logger.debug(f"  - Max concurrent workers: {Config.MaxWorkers}")
            Config.logger.debug(f"  - HTTP Proxy: {Config.HTTPProxy or 'None'}")
            Config.logger.debug(f"  - Log output file: {Config.LogFile or 'stdout'}")

        handle_auth(anime, login, register)
        selected_query, download_parts = handle_search(anime, query, latest, deep_search, search_index, max_results, download_parts, verbose)
        if Config.LoggerV:
            Config.logger.debug(f"Search completed, proceeding with query: '{selected_query}'")
        handle_download(anime, download_parts, res, output_dir, download_now, verbose)
        Config.logger.info("Application execution completed successfully")
        click.echo("Thank you for using Anime3rbDL! Made with ♥ by MrJo0x01")
    except KeyboardInterrupt:
        Config.exit("[INFO] Operation cancelled by user.")
    except Exception as e:
        if debug:
            traceback.print_exc()
        Config.exit(f"[ERROR] {e}")


if __name__ == "__main__":
    click.echo(LOGO)
    main()

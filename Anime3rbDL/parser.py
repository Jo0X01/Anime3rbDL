import copy
import json
import random
import re
import time
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup as bs4
import dateutil.parser
import isodate

from Anime3rbDL.client import Anime3rbHTTPClient
from Anime3rbDL.config import Cache, Config
from Anime3rbDL.enums import (
    ContributorEnum,
    CustomTypes,
    LastAddedEpisodesResutlsEnum,
    LatestAddedAnimeResultsEnum,
    ResolutionURLs,
    TargetAnimeEnum,
    TranslateArabic,
    VideoObjectEnum,
)
from Anime3rbDL.exceptions import (
    NotFoundError,
    ParseError,
    SearchError,
)


class ParserUtils:
    """Core utility class for parsing Anime3rb website data.

    Handles URL normalization, filename sanitization, HTML/JSON parsing,
    episode and series metadata extraction, resolution processing,
    authentication, and search result population. Integrates with Cache
    and Config for state management and logging.

    All methods are static for utility-style usage without instantiation.
    """

    @staticmethod
    def _parse_url(url: str) -> str:
        """Normalize and sanitize a given URL.

        Args:
            url (str): The input URL or path.

        Returns:
            str: A valid, normalized URL string.
        """
        parsed = urlparse(url)
        netloc = parsed.netloc
        path = parsed.path
        if not netloc and path.startswith("/"):
            parts = path.lstrip("/").split("/", 1)
            netloc = parts[0]
            path = "/" + parts[1] if len(parts) > 1 else ""
        return urlunparse((parsed.scheme or "https", netloc, path, "", "", "")).replace(
            " ", "-"
        )

    @staticmethod
    def _extract_resolution_from_label(label: str) -> str:
        """Extract resolution from a label string.

        Args:
            label (str): The label containing resolution info.

        Returns:
            str: The extracted resolution (e.g., "1080p").
        """
        match = re.search(r"\[([0-9]+p)\]", label)
        return match.group(1) if match else "unknown"

    @staticmethod
    def _parse_token(soup: bs4) -> str:
        """Extract CSRF token from an HTML soup object.

        Args:
            soup (bs4): BeautifulSoup-parsed HTML.

        Returns:
            str: The CSRF token.

        Raises:
            SystemExit: If token not found in HTML.
        """
        _token = soup.find("meta", {"name": "csrf-token", "content": True})
        if not _token or "content" not in _token.attrs:
            Config.logger.error("CSRF token not found in page.")
            raise ParseError("CSRF token not found in page.")
        return _token.attrs["content"]

    @staticmethod
    def format_bytes(size: int) -> str:
        """Convert bytes into a human-readable format.

        Args:
            size (int): File size in bytes.

        Returns:
            str: Formatted size string (e.g., "1.23MB").
        """
        if size == 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        index = 0
        size = float(size)
        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1
        return f"{size:.2f}{units[index]}"

    @staticmethod
    def parse_filename(filename: str, replacement: str = "_") -> str:
        """Sanitize a filename by removing or replacing invalid characters.

        Args:
            filename (str): Original filename.
            replacement (str): Character used to replace invalid chars.

        Returns:
            str: Safe filename string.
        """
        # Remove or replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, replacement, filename)

        # Additional cleaning
        replacements = [
            (r"[-_]{2,}", "-"),  # collapse multiple - or _
            (r"[~]+", " "),  # replace ~ with space
            (r"\s*-\s*", " - "),  # normalize spacing around dashes
            (r"\s+", " "),  # collapse multiple spaces
        ]
        for pattern, repl in replacements:
            filename = re.sub(pattern, repl, filename)

        filename = filename.rstrip(". ")

        # Handle reserved names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        if filename.upper().split(".")[0] in reserved_names:
            filename = f"{replacement}{filename}"

        # Remove specific suffix
        return filename.replace(" - Anime3rb أنمي عرب", "")

    @staticmethod
    def parse_query(query: str) -> bool:
        """Parse user query (slug or URL) and update cache accordingly.

        Args:
            query (str): User query string (anime title or URL).

        Returns:
            bool: True if query is a full URL, False otherwise.
        """
        query = str(query).strip()
        is_url = query.startswith(Config.WebsiteURL)

        if Config.LoggerV:
            Config.logger.debug(f"Parsing query: '{query}'")
            Config.logger.debug(
                f"Query detected as {'URL' if is_url else 'search term'}"
            )

        slug = query

        if is_url:
            query = ParserUtils._parse_url(query)
            path_parts = urlparse(query).path.strip("/").split("/")
            slug = (
                path_parts[1]
                if len(path_parts) > 1 and path_parts[0] in ["titles", "episode"]
                else path_parts[-1]
            )
            if Config.LoggerV:
                Config.logger.debug(f"Parsed URL path parts: {path_parts}")
                Config.logger.debug(f"Extracted slug: {slug}")

        slug_url = slug.replace(" ", "-").lower()

        Cache.USER_INPUT_URL = slug_url
        Cache.ANIME_TITLE = "[Anime3rbDL] "+slug.replace("-", " ").capitalize()
        Cache.ANIME_URL = Config.TitleURL + slug_url

        if not is_url:
            Cache.ANIME_QUERY_SEARCH = slug_url
            Cache.ANIME_SEARCH_URL = f"{Config.SearchURL}?q={slug_url}"
            if Config.LoggerV:
                Config.logger.debug(f"Set search URL: {Cache.ANIME_SEARCH_URL}")

        if Config.LoggerV:
            Config.logger.debug(
                f"Cache updated - Title: '{Cache.ANIME_TITLE}', URL: '{Cache.ANIME_URL}'"
            )

        return is_url

    @staticmethod
    def parse_skip_parts(_input: str) -> None:
        """Parse episode selection string into a list of zero-based episode indices.

        Args:
            _input (str): Selection string (e.g., "1-3,5,7-9").

        Returns:
            None: Updates Config.DownloadParts directly.

        Raises:
            ValueError: If invalid format is provided.
        """
        raw = str(_input).lower().replace(" ", "").strip()
        skip_episodes: list[int] = []

        if Config.LoggerV:
            Config.logger.debug(f"Parsing episode selection: '{_input}' (raw: '{raw}')")

        if not raw or raw == "all":
            Config.DownloadParts = []
            Config.logger.info("Downloading all episodes")
            if Config.LoggerV:
                Config.logger.debug("Episode selection set to download all episodes")
            return

        try:
            for part in raw.split(","):
                if not part:
                    continue
                if "-" in part:
                    start, end = map(int, part.split("-", 1))
                    if start > end:
                        raise ValueError(f"Invalid range '{part}'")
                    skip_episodes.extend(range(start - 1, end))
                    if Config.LoggerV:
                        Config.logger.debug(
                            f"Parsed range '{part}' to episodes {start-1} to {end-1}"
                        )
                else:
                    skip_episodes.append(int(part) - 1)
                    if Config.LoggerV:
                        Config.logger.debug(
                            f"Parsed single episode '{part}' to index {int(part) - 1}"
                        )
        except ValueError as e:
            if Config.LoggerV:
                Config.logger.debug(f"Error parsing episode selection: {e}")
            raise ParseError(f"Invalid skip parts format: {_input}") from e

        skip_episodes = sorted(set(skip_episodes))

        Config.DownloadParts = skip_episodes
        if skip_episodes:
            episode_list = ",".join(map(str, [x + 1 for x in skip_episodes]))
            Config.logger.info(f"Downloading only episodes: {episode_list}")
            if Config.LoggerV:
                Config.logger.debug(
                    f"Final episode indices to download: {skip_episodes}"
                )
        else:
            Config.logger.info("No episodes selected (empty input).")
            if Config.LoggerV:
                Config.logger.debug("No episodes selected after parsing")

    @staticmethod
    def _parse_direct_link(url: str) -> str:
        """Resolve a direct video download link from a given URL.

        Args:
            url (str): Candidate download link.

        Returns:
            str | None: Direct video link if found, else None.
        """
        response = Anime3rbHTTPClient.head_req(url)
        if response is None:
            return None
        _content_type = {k.lower(): v.lower() for k, v in response.headers.items()}.get(
            "content-type", ""
        )
        if _content_type.startswith("video/mp4"):
            return response.url

        if _content_type.startswith("text/html"):
            content = Anime3rbHTTPClient.get_req(response.url)
            soup = bs4(content, "html.parser")
            direct_link = soup.find(
                lambda tag: (
                    tag.name == "a"
                    and (tag.has_attr("wire:id") or tag.has_attr("wire:key"))
                    and tag.has_attr("href")
                    and re.compile(r"https://anime3rb\.com/download/.*").match(tag["href"])
                )
            )
            if direct_link and "href" in direct_link.attrs:
                return ParserUtils._parse_direct_link(direct_link.attrs["href"])
        return None

    @staticmethod
    def _fetch_and_format(
        _url: str, headers={}, _action_mode: bool = False, _response: bool = False
    ) -> tuple[dict, bytes, bs4]:
        """Fetch and parse HTML page into JSON and BeautifulSoup.

        Args:
            _url (str): URL to fetch.
            headers (dict): Optional request headers.
            _action_mode (bool): Enable search API snapshot parsing.
            _response (bool): If True, return raw response.

        Returns:
            tuple: (data/json or text, raw HTML, soup)
        """
        PageHTML = Anime3rbHTTPClient.get_req(_url, headers)
        if not PageHTML:
            Config.logger.error("ConnectionError => Bad Page Source")
            raise ParseError("ConnectionError => Bad Page Source")
        soup = bs4(PageHTML, "html.parser")
        if not soup:
            Config.logger.error("HTMLParserError => UnExpected Response")
            raise ParseError("HTMLParserError => UnExpected Response")
        if _response:
            return None, PageHTML, soup

        if _action_mode:
            script_tag = soup.find("form", {"action": Config.SearchURL}).attrs.get(
                "wire:snapshot"
            )
            if not script_tag:
                Config.logger.error(
                    "HTMLTagError => Missing or empty JSON-LD wire:snapshot tag"
                )
                raise ParseError(
                    "HTMLTagError => Missing or empty JSON-LD wire:snapshot tag"
                )
            return script_tag, PageHTML, soup
        else:
            script_tag = soup.find("script", {"type": "application/ld+json"})
            if not script_tag or not script_tag.string:
                Config.logger.error(
                    "HTMLTagError => Missing or empty JSON-LD script tag"
                )
                raise ParseError("HTMLTagError => Missing or empty JSON-LD script tag")
        try:
            data = json.loads(script_tag.string)
        except json.JSONDecodeError as e:
            Config.logger.error(f"JSONError => {e}")
            Config.exit(f"JSONError => {e}")
        return data, PageHTML, soup

    @staticmethod
    def parse_qualities_data(_soup, get_res_only: str = None,index=0) -> ResolutionURLs:
        """Parse available download qualities and links from an episode's HTML page.

        This function extracts the download URLs, file sizes, and resolution labels
        from the episode page. It also updates the global `Cache` object with
        cumulative sizes and metadata for each resolution.

        Args:
            _html (str | bytes): The HTML content of the episode page.
            get_res_only (str, optional): If specified, only parse a specific resolution.
                Acceptable values:
                    - "low" or "480p"
                    - "mid" or "720p"
                    - "high" or "1080p"
                    - "unknown"

        Returns:
            ResolutionURLs: An object containing the parsed download links, file sizes,
                and metadata for each resolution (low, mid, high, unknown).

        Raises:
            SystemExit: If no download links are found in the HTML content.

        Side Effects:
            - Updates `Cache.DownloadInfo` for each resolution with:
                Size, FormatedSize, DownloadLink, DirectLink, FileName
            - Updates `Cache.TotalSize` cumulative sizes and formatted sizes.
            - Logs info and warnings for each parsed quality.
            - Introduces a random short delay between link resolutions to avoid rapid requests.
        """
        if Config.LoggerV:
            Config.logger.debug(
                f"Parsing qualities data for resolution filter: {get_res_only}"
            )
        title = _soup.find("title").string

        if Config.LoggerV:
            Config.logger.debug(f"Page title: {title}")

        translates = _soup.find_all("div", {"wire:key": re.compile(r"download\.[a-zA-Z0-9]+")})
        if len(translates) == 0:
            Config.logger.warning("No Episode Translators Found, Skip...")
            return None

        if len(translates) > 1:
            _trans = []
            for tran_soup in translates:
                _trans.append(tran_soup.find("small").string.replace("ترجمة","").strip())
            Config.logger.info(f"Found Episode Translators: {', '.join(_trans)}")
            selected_soup = None
            for tran_soup in translates:
                translate = tran_soup.find("small").string.replace("ترجمة","").strip()
                if Config.EpisodeTranslator.lower() in translate.lower().replace("-"," "):
                    selected_soup = tran_soup
                    break
            if selected_soup is None:
                selected_soup = translates[0]
                translate = translates[0].find("small").string.replace("ترجمة","").strip()
            _soup = selected_soup
        else:
            _soup = translates[0]
            translate = translates[0].find("small").string.replace("ترجمة","").strip()

        Config.logger.info(f"Using Episode Translate: {translate}")
        
        
        qualities = []
        for div in _soup.find_all("div"):
            if div.find("label") and div.find("a"):
                qualities.append(
                    (
                        div.find("a").attrs["href"],
                        div.find("a").string,
                        div.find("label").string,
                    )
                )

        if Config.LoggerV:
            Config.logger.debug(f"Found {len(qualities)} quality options")

        if not qualities:
            Config.logger.error("ParserError => No DownloadLinks Found")
            raise ParseError("ParserError => No DownloadLinks Found")

        for link, size, label in qualities:
            if Config.LoggerV:
                Config.logger.debug(
                    f"Processing quality - Link: {link}, Size: {size}, Label: {label}"
                )

            if "HEVC" in label:
                if Config.LoggerV:
                    Config.logger.debug("Skipping HEVC quality")
                continue

            fsize, unit = re.search(
                r"\[([\d\.]+)\s*(غيغابايت|ميغابايت)\]", size
            ).groups()
            size = int(
                round(float(fsize) * 1024 * 1024 * (1024 if "غيغابايت" in unit else 1))
            )
            fsize = ParserUtils.format_bytes(size)
            res = ParserUtils._extract_resolution_from_label(label)

            if Config.LoggerV:
                Config.logger.debug(f"Parsed resolution: {res}, Size: {fsize}")

            if (
                not get_res_only is None
                and not Config.DefaultResoultion.get(get_res_only) == res
            ):
                if Config.LoggerV:
                    Config.logger.debug(
                        f"Skipping {res} - doesn't match filter {get_res_only}"
                    )
                continue

            file_name = ParserUtils.parse_filename(title) + ".mp4"
            direct_link = ParserUtils._parse_direct_link(link)
            if direct_link is None:
                Config.logger.error(f"Fetching DirectLink: {link}")
                Config.exit(f"[ERR] Fetching Direct Link: {link}")
            time.sleep(random.uniform(1, 3))  # avoid rapid requests

            if Config.LoggerV:
                Config.logger.debug(f"Resolved direct link: {direct_link}")

            Config.logger.info(
                f"Get [Episode: {index}] quality: {res} Size: {fsize}"
            )
            if direct_link is None:
                Config.logger.warning(
                    f"Failed to resolve direct link for {res} quality."
                )
                continue

            # Assign to Cache based on resolution
            if res == "1080p" and (
                get_res_only is None or get_res_only in ["high", "1080p"]
            ):
                Cache.TotalSize.High += size
                Cache.TotalSize.FHigh = ParserUtils.format_bytes(Cache.TotalSize.High)
                Cache.DownloadInfo.High.Size = size
                Cache.DownloadInfo.High.FormatedSize = fsize
                Cache.DownloadInfo.High.DownloadLink = link
                Cache.DownloadInfo.High.DirectLink = direct_link
                Cache.DownloadInfo.High.FileName = file_name
                Cache.DownloadInfo.High.Index = index
            elif res == "720p" and (
                get_res_only is None or get_res_only in ["mid", "720p"]
            ):
                Cache.TotalSize.Mid += size
                Cache.TotalSize.FMid = ParserUtils.format_bytes(Cache.TotalSize.Mid)
                Cache.DownloadInfo.Mid.Size = size
                Cache.DownloadInfo.Mid.FormatedSize = fsize
                Cache.DownloadInfo.Mid.DownloadLink = link
                Cache.DownloadInfo.Mid.DirectLink = direct_link
                Cache.DownloadInfo.Mid.FileName = file_name
                Cache.DownloadInfo.Mid.Index = index
            elif res == "480p" and (
                get_res_only is None or get_res_only in ["low", "480p"]
            ):
                Cache.TotalSize.Low += size
                Cache.TotalSize.FLow = ParserUtils.format_bytes(Cache.TotalSize.Low)
                Cache.DownloadInfo.Low.Size = size
                Cache.DownloadInfo.Low.FormatedSize = fsize
                Cache.DownloadInfo.Low.DownloadLink = link
                Cache.DownloadInfo.Low.DirectLink = direct_link
                Cache.DownloadInfo.Low.FileName = file_name
                Cache.DownloadInfo.Low.Index = index
            elif get_res_only is None or get_res_only == "unknown":
                Cache.TotalSize.UnKnown += size
                Cache.TotalSize.FUnKnown = ParserUtils.format_bytes(
                    Cache.TotalSize.UnKnown
                )
                Cache.DownloadInfo.UnKnown.Size = size
                Cache.DownloadInfo.UnKnown.FormatedSize = fsize
                Cache.DownloadInfo.UnKnown.DownloadLink = link
                Cache.DownloadInfo.UnKnown.DirectLink = direct_link
                Cache.DownloadInfo.UnKnown.FileName = file_name
                Cache.DownloadInfo.UnKnown.Index = index
        return Cache.DownloadInfo,translate

    @staticmethod
    def _parse_episode_data(episode: dict, _soup: bs4, index: int = 0) -> VideoObjectEnum:
        """Parse JSON-LD episode object and map into VideoObjectEnum.

        Args:
            episode (dict): Episode JSON data.
            _soup (bs4): BeautifulSoup parsed HTML.
            index (int): Episode index.

        Returns:
            VideoObjectEnum: Parsed episode object.
        """
        video: list[dict] = episode.get("video")
        if not video:
            Config.logger.error("SearchError => No Available Videos Found")
            raise SearchError("SearchError => No Available Videos Found")
        _qual = ParserUtils.parse_qualities_data(_soup, index=index)
        if _qual is None:
            return None
        translate, _qualities = _qual
        for vid in video:
            if translate in vid["name"]:
                video = vid
                break
        Cache.TARGET_EPISODE_ANIME = VideoObjectEnum(
            _soup,
            CustomTypes(episode.get("@type")),
            ParserUtils.parse_filename(episode.get("name")),
            episode.get("url"),
            dateutil.parser.parse(episode.get("datePublished")),
            episode.get("inLanguage"),
            episode.get("description"),
            video.get("name"),
            ParserUtils.parse_filename(video.get("name")),
            video.get("thumbnailUrl"),
            video.get("embedUrl"),
            video.get("playerType"),
            video.get("description"),
            dateutil.parser.parse(video.get("uploadDate")),
            video.get("isFamilyFriendly"),
            isodate.parse_duration(video.get("duration")),
            copy.deepcopy(_qualities),
            episode.get("isPartOf", {}).get("url"),
        )
        return Cache.TARGET_EPISODE_ANIME

    @staticmethod
    def _parse_tv_serise_data(series: dict, _html: bytes,_soup:bs4) -> TargetAnimeEnum:
        """Parse JSON-LD TVSeries object into TargetAnimeEnum.

        Args:
            series (dict): Series JSON data.
            _html (bytes): Raw HTML content.

        Returns:
            TargetAnimeEnum: Parsed TV series object.
        """
        episodes: list[dict] = series.get("episode")
        if not episodes:
            Config.logger.error("SearchError => No episodes found for TVSeries")
            raise SearchError("SearchError => No episodes found for TVSeries")
        Cache.TARGET_TVSeries_ANIME = TargetAnimeEnum(
            _html,
            CustomTypes(series.get("@type")),
            series.get("name"),
            ParserUtils.parse_filename(series.get("name")).capitalize(),
            "[Anime3rbDL] "+ParserUtils.parse_filename(series.get("name")).capitalize(),
            series.get("description"),
            series.get("url"),
            dateutil.parser.parse(series.get("datePublished")),
            [_["embedUrl"] for _ in series.get("trailer")],
            series.get("image"),
            series.get("inLanguage"),
            [
                TranslateArabic.get(_genre, "UnKnown")
                for _genre in series.get("genre", [])
            ],
            [
                ParserUtils.parse_filename(_name)
                for _name in series.get("alternateName", [])
            ],
            [
                ContributorEnum(
                    _contr["name"], _contr["url"], TranslateArabic.get(_contr["role"])
                )
                for _contr in series.get("contributor", [])
            ],
            series.get("aggregateRating", {}).get("ratingValue"),
            TranslateArabic.get(_soup.find_all("td",string=lambda t: t and t.strip() in ("قيد البث", "منتهي"))[0].string),
            len(episodes),
            [_url["url"] for _url in episodes],
        )
        return Cache.TARGET_TVSeries_ANIME

    @staticmethod
    def parse_title_page():
        """Parse anime title page to determine content type and extract metadata.

        Fetches the page, parses JSON-LD data to identify if it's an Episode, TV Series,
        or Movie. For movies, fetches the first episode page to get download info.
        Populates Cache with the parsed anime object based on type.

        Returns:
            TargetAnimeEnum | VideoObjectEnum: Parsed anime object (series or episode/movie).

        Raises:
            ParseError: If unexpected content type or parsing fails.

        Side Effects:
            - Updates Cache.ANIME_URL with normalized URL.
            - Populates Cache.TARGET_TVSeries_ANIME or Cache.TARGET_EPISODE_ANIME.
            - Logs detected type and processing steps.
        """
        if Config.LoggerV:
            Config.logger.debug(f"Parsing title page: {Cache.ANIME_URL}")

        data, _html, _soup = ParserUtils._fetch_and_format(Cache.ANIME_URL)
        _type = CustomTypes(data.get("@type"))

        if Config.LoggerV:
            Config.logger.debug(f"Detected content type: {_type}")

        if _type == CustomTypes.EPISODE and data.get("video"):
            Config.logger.info("Anime is Episode")
            if Config.LoggerV:
                Config.logger.debug("Processing as episode with video data")
            return ParserUtils._parse_episode_data(data, _soup, 0)
        elif _type == CustomTypes.SERIES:
            Config.logger.info("Anime is Series")
            if Config.LoggerV:
                Config.logger.debug("Processing as TV series")
            return ParserUtils._parse_tv_serise_data(data,_html,_soup)
        if _type == CustomTypes.MOVIE or (
            _type == CustomTypes.EPISODE and data.get("video") is None
        ):
            Config.logger.info("Anime is Movie")
            if Config.LoggerV:
                Config.logger.debug("Processing as movie, fetching episode data")
            data, _html, _soup = ParserUtils._fetch_and_format(
                f"{Config.EpisodeURL}{Cache.USER_INPUT_URL}/1"
            )
            _type = CustomTypes(data.get("@type"))
            if Config.LoggerV:
                Config.logger.debug(f"Movie episode type: {_type}")
            if not _type == CustomTypes.EPISODE:
                Config.logger.error(f"UnKnownError => UnExpected Type: [{_type}]")
                raise ParseError(f"UnKnownError => UnExpected Type: [{_type}]")
            return ParserUtils._parse_episode_data(data, _soup, 0)
        Config.logger.error(f"UnKnownError => UnExpected Type: [{_type}]")
        raise ParseError(f"UnKnownError => UnExpected Type: [{_type}]")


    @staticmethod
    def parse_search_page():
        """Parse full search results from Anime3rb search API with pagination.

        Fetches search results page by page until no more results or max limit reached.
        Parses JSON data to extract anime metadata and populates Cache.SearchResult.

        Returns:
            SearchResultEnum: Filled with parsed search results.

        Side Effects:
            - Updates Cache.SearchResult with anime list.
            - Logs pagination progress and result counts.
        """
        Cache.SearchResult.Results = []
        page = 1
        while True:
            _url = f"{Cache.ANIME_SEARCH_URL}"
            if page > 1:
                _url += f"&page={page}&lang=en"
            json_data, _, _ = ParserUtils._fetch_and_format(_url, {"referer": _url})
            json_data = json_data.get("itemListElement", [])
            for item in json_data:
                item = item["item"]
                if not isinstance(item, dict):
                    continue
                Cache.SearchResult.Add(
                    item["@type"],
                    item["name"].replace(" - Anime3rb أنمي عرب", ""),
                    ParserUtils.parse_filename(item["name"]).replace(
                        " - Anime3rb أنمي عرب", ""
                    ),
                    item["url"],
                    item["inLanguage"],
                    item["image"],
                    item["description"],
                    item.get("numberOfEpisodes", 1),
                    [TranslateArabic.get(_g) for _g in item.get("genre", [])],
                    dateutil.parser.parse(item["datePublished"]),
                    float(item.get("aggregateRating", {}).get("ratingValue", 0.0)),
                )
            if json_data == [] or len(Cache.SearchResult.Results) > Config.MAX_RESULT:
                break
            page += 1
        return Cache.SearchResult

    @staticmethod
    def parse_tiny_search_page():
        """Perform fast search using Anime3rb's live search API.

        Uses Livewire API to get quick search results without full pagination.
        Parses HTML snippet response to extract anime titles, links, images, and metadata.

        Returns:
            TinySearchResultEnum: Filled with lightweight search results.

        Raises:
            NotFoundError: If no search results found.
            SearchError: If API request fails.

        Side Effects:
            - Updates Cache.TinySearchResult with anime list.
            - Logs search query and result count.
        """
        _snapshot, _, soup = ParserUtils._fetch_and_format(
            Config.WebsiteURL, _action_mode=True
        )
        _token = ParserUtils._parse_token(soup)
        try:
            _snapshot = json.dumps(json.loads(_snapshot))
        except Exception:
            Config.logger.error("Snapshot parse failed")
            raise ParseError("Snapshot parse failed")

        _response = Anime3rbHTTPClient.post_req(
            Config.SearchAPI,
            payload={
                "components": [
                    {
                        "calls": [],
                        "snapshot": _snapshot,
                        "updates": {"query": Cache.USER_INPUT_URL, "deep": True},
                    }
                ],
                "_token": _token,
            },
            headers={
                "content-type": "application/json",
                "referer": Config.TitleURL + "list",
                "origin": Config.WebsiteURL,
                "x-livewire": "",
            },
        )
        if not _response:
            Config.logger.error("Search API Request Failed")
            raise SearchError("Search API Request Failed")

        try:
            html_snippet = _response["components"][0]["effects"]["html"]
        except Exception:
            Config.logger.error("Unexpected search API response")
            raise ParseError("Unexpected search API response")

        soup = bs4(html_snippet, "html.parser")
        _results = soup.find_all(
            "a", href=re.compile(r"^https://anime3rb\.com/titles/.*")
        )
        if not _results:
            Config.logger.error("No Results")
            raise NotFoundError("No Results")

        for a in _results:
            try:
                details = a.find("div", {"class": "details"})
                if not details:
                    continue

                # title + description
                title_tag = details.find("h4", {"class": "text-lg"})
                desc_tag = details.find("h5", {"class": "text-sm"})
                if not title_tag or not desc_tag:
                    continue

                title = title_tag.get_text(strip=True)
                description = desc_tag.get_text(strip=True)

                # link + image
                link = a.get("href", "")
                img_tag = a.select_one("img")
                image = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                # badges: rate, count, year
                badges = details.select(".badge")
                rate = ParserUtils._safe_extract_badge(badges, 0, "0.0", float)
                count = ParserUtils._safe_extract_badge(badges, 1, "-1", int)
                year = ParserUtils._safe_extract_badge(badges, 2, "-1", int)

                Cache.TinySearchResult.Add(
                    title,
                    ParserUtils.parse_filename(title),
                    link,
                    image,
                    description,
                    float(rate),
                    int(count),
                    int(year),
                )
            except Exception as e:
                Config.logger.warning(f"Skipped a broken entry: {e}")
                continue

        return Cache.TinySearchResult

    @staticmethod
    def _safe_extract_badge(badges, idx, default, cast_type):
        """Safely extract numeric badge value from a list of HTML badge elements.

        Args:
            badges (list): List of badge elements.
            idx (int): Index of badge to extract.
            default (str | int | float): Default value if extraction fails.
            cast_type (type): Type to cast extracted value to.

        Returns:
            int | float | str: Extracted value or default fallback.
        """
        try:
            if idx >= len(badges):
                return cast_type(default)
            text = badges[idx].get_text(strip=True)
            match = re.search(r"([0-9\.]+)", text)
            return cast_type(match.group(1)) if match else cast_type(default)
        except Exception:
            return cast_type(default)

    @staticmethod
    def yield_episodes_info(get_res_only: str = None):
        """Generator that parses and yields episode data for a TV series.

        Iterates through all episode URLs in the series, fetches each page,
        parses metadata and download qualities. Yields EpisodeEnum objects
        while respecting download selection (Config.DownloadParts).

        Args:
            get_res_only (str, optional): Filter to specific resolution ("low", "mid", "high").

        Yields:
            EpisodeEnum: Parsed episode with metadata, qualities, and download links.

        Side Effects:
            - Resets Cache.EpisodesDownloadData and repopulates.
            - Adds episodes to Cache.TARGET_TVSeries_ANIME.
            - Logs episode processing, skips, and warnings for missing/multiple videos.
        """
        if Config.LoggerV:
            Config.logger.debug(
                f"Starting episode info parsing for resolution filter: {get_res_only}"
            )

        if not Cache.TARGET_TVSeries_ANIME:
            if Config.LoggerV:
                Config.logger.debug("No TV series anime found in cache")
            return

        # Reset cached download data
        Cache.EpisodesDownloadData = []

        total_episodes = len(Cache.TARGET_TVSeries_ANIME.EpisodesURLs)
        if Config.LoggerV:
            Config.logger.debug(f"Processing {total_episodes} episodes")

        for index, episode_url in enumerate(Cache.TARGET_TVSeries_ANIME.EpisodesURLs):
            if Config.LoggerV:
                Config.logger.debug(
                    f"Processing episode {index + 1}/{total_episodes}: {episode_url}"
                )
            if Config.DownloadParts and index not in Config.DownloadParts:
                episode_id = "/".join(episode_url.split("/")[-2:])
                Config.logger.warning(f"Skipping Episode [{episode_id}]")
                if Config.LoggerV:
                    Config.logger.debug(
                        f"Episode {index} skipped due to download parts configuration"
                    )
                continue

            _json, _html, _soup = ParserUtils._fetch_and_format(episode_url)
            _video = _json.get("video", [])

            if Config.LoggerV:
                Config.logger.debug(f"Episode {index + 1} has {len(_video)} video(s)")

            if not _video:
                Config.logger.warning(
                    "Episode does not contain any videos, skipping..."
                )
                if Config.LoggerV:
                    Config.logger.debug(
                        f"Episode {index + 1} skipped - no videos found"
                    )
                continue

            qualities_tuple = ParserUtils.parse_qualities_data(_soup, get_res_only, index+1)
            if qualities_tuple is None:
                continue
            qualities, _ = qualities_tuple
            qualities = copy.deepcopy(qualities)
            if len(_video) > 1:
                Config.logger.warning(
                    "Found multiple translations, taking the first one... ()"
                )
                if Config.LoggerV:
                    Config.logger.debug(
                        f"Episode {index + 1} has multiple translations, using first ()"
                    )

            _video = _video[0]
            episode_obj = Cache.TARGET_TVSeries_ANIME.Add(
                index,
                _json.get("name"),
                ParserUtils.parse_filename(_json.get("name")),
                _json.get("description"),
                _json.get("url"),
                dateutil.parser.parse(_json.get("datePublished")),
                _html,
                _json.get("inLanguage"),
                ParserUtils.parse_filename(_video.get("name")),
                _video.get("thumbnailUrl"),
                _video.get("embedUrl"),
                _video.get("playerType"),
                _video.get("description"),
                dateutil.parser.parse(_video.get("uploadDate")),
                _video.get("isFamilyFriendly"),
                isodate.parse_duration(_video.get("duration")),
                qualities,
                _video.get("isPartOf", {}).get("url"),
            )

            Cache.EpisodesDownloadData.append(episode_obj)
            if Config.LoggerV:
                Config.logger.debug(
                    f"Episode {index + 1} parsed and added to download data"
                )
            yield episode_obj
        if Cache.EpisodesDownloadData == []:
            Cache.EpisodesDownloadData.append(Cache.TARGET_EPISODE_ANIME)
            yield Cache.TARGET_EPISODE_ANIME
        return
    @staticmethod
    def parse_episodes_info(get_res_only: str = None):
        """Parse all episodes from a series and return as list.

        Uses yield_episodes_info generator to collect all episodes into a list.
        Useful when you need all episodes at once rather than streaming.

        Args:
            get_res_only (str, optional): Filter to specific resolution.

        Returns:
            list[EpisodeEnum]: Complete list of parsed episodes.

        Side Effects:
            - Fully populates Cache.EpisodesDownloadData.
            - Logs total episodes processed.
        """
        return list(ParserUtils.yield_episodes_info(get_res_only))

    @staticmethod
    def parse_resolution(res: str, default: str = None):
        """Normalize resolution string (e.g., "720" -> "720p").

        Args:
            res (str): Resolution string or number.
            default (str, optional): Default resolution fallback.

        Returns:
            str | None: Normalized resolution or fallback.
        """
        res = str(res).lower()
        if res.isdigit():
            res = f"{res}p"
        if res.endswith("p"):
            if res in list(Config.DefaultResoultion.values()):
                return res
            return Config.DefaultResoultion.get(default)
        return Config.DefaultResoultion.get(res, Config.DefaultResoultion.get(default))

    @staticmethod
    def parse_register_page():
        """Register new Anime3rb account using stored credentials.

        Fetches registration page, extracts CSRF token, submits registration form
        with Config.Username, Config.Email, Config.Password.

        Returns:
            bool: True if registration successful (redirects to main site), False otherwise.

        Side Effects:
            - Logs success/failure with credentials.
            - Updates session cookies on success.
        """
        _, soup, _ = ParserUtils._fetch_and_format(Config.RegisterAPI, _response=True)
        _token = ParserUtils._parse_token(soup)
        _response = Anime3rbHTTPClient.post_req(
            Config.RegisterAPI,
            {
                "_token": _token,
                "name": Config.Username,
                "email": Config.Email,
                "password": Config.Password,
                "password_confirmation": "RegisterAPI",
            },
            return_response=True,
        )

        if Config.WebsiteURL.startswith(_response.url):
            Config.logger.info(
                f"Account Created Success: {Config.Username}:{Config.Email}:{Config.Password}"
            )
            return True
        Config.logger.warning(
            f"Register Failed: {Config.Username}:{Config.Email}:{Config.Password}"
        )
        return False

    @staticmethod
    def parse_login_page():
        """Authenticate to Anime3rb using stored email and password.

        Fetches login page, extracts CSRF token, submits login form.
        Checks for successful redirect to determine login status.

        Returns:
            bool: True if login successful, False otherwise.

        Side Effects:
            - Logs success/failure with username.
            - Establishes authenticated session on success.
        """
        _, soup, _ = ParserUtils._fetch_and_format(Config.LoginAPI, _response=True)
        _token = ParserUtils._parse_token(soup)
        _response = Anime3rbHTTPClient.post_req(
            Config.LoginAPI,
            {"_token": _token, "email": Config.Email, "password": Config.Password},
            return_response=True,
        )
        if Config.WebsiteURL.startswith(_response.url):
            Config.logger.info(f"Login Success: {Config.Username}")
            return True
        Config.logger.warning(f"Login Failed: {Config.Username}:{Config.Password}")
        return False

    @staticmethod
    def __find_itemlist_by_name(data, target_name):
        """Recursively search for an ItemList with the specified name in the data structure.

        Args:
            data: The data structure to search in (dict or list).
            target_name (str): The name of the ItemList to find.

        Returns:
            The itemListElement of the found ItemList, or None if not found.
        """
        if isinstance(data, dict):
            # Check if this dict is an ItemList with the right name
            if (
                data.get("@type") == CustomTypes.ITEM_LIST.value
                and data.get("name") == target_name
            ):
                return data.get("itemListElement", data)

            # Otherwise recurse into its values
            for value in data.values():
                result = ParserUtils.__find_itemlist_by_name(value, target_name)
                if result:
                    return result

        elif isinstance(data, list):
            # Recurse into each element
            for item in data:
                result = ParserUtils.__find_itemlist_by_name(item, target_name)
                if result:
                    return result

        return None

    @staticmethod
    def parse_get_latest():
        """Fetch and parse latest anime and episodes from homepage.

        Parses JSON-LD data from main page to extract recently added anime and episodes.
        Handles episode pagination by following "Next Episodes" links. Associates episodes
        with their parent anime series.

        Returns:
            tuple[LatestAddedAnimeResultsEnum, LastAddedEpisodesResutlsEnum]:
                Latest anime and episodes data.

        Side Effects:
            - Populates Cache.LastAddedAnimes and Cache.LastAddedEpisodes.
            - Limits results to Config.MAX_RESULT.
            - Logs parsing progress and counts.
        """
        _resp,_,_ = ParserUtils._fetch_and_format(Config.WebsiteURL)
        _main = _resp["mainEntity"]["itemListElement"]  # list value
        Cache.LastAddedAnimes = LatestAddedAnimeResultsEnum()
        Cache.LastAddedEpisodes = LastAddedEpisodesResutlsEnum()
        
        last_added_animes = ParserUtils.__find_itemlist_by_name(
            _main, CustomTypes.LAST_ADDED_ANIMES.value
        )
        for anime in last_added_animes:
            anime = anime.get("item")
            Cache.LastAddedAnimes.Add(
                CustomTypes(anime.get("@type")),
                anime.get("name"),
                ParserUtils.parse_filename(anime.get("name")).replace("الحلقة","").replace("الأخيرة","").strip(),
                anime["url"],
                anime.get("image"),
                [TranslateArabic.get(_g) for _g in anime.get("genre", [])],
                anime.get("description"),
                anime.get("aggregateRating").get("ratingValue"),
                dateutil.parser.parse(anime.get("datePublished")),
            )
        
        while Cache.LastAddedEpisodes.Count <= Config.MAX_RESULT:
            newest_episodes = ParserUtils.__find_itemlist_by_name(
                _main, CustomTypes.NEWEST_EPISODES.value
            )
            for new_episode in newest_episodes:
                _url = new_episode["url"].split("/")
                num,url = int(_url[-1]),"/".join(_url[:-1]).replace("episode","titles")
                Cache.LastAddedEpisodes.Add(
                    CustomTypes.EPISODE,
                    new_episode["name"],
                    ParserUtils.parse_filename(new_episode["name"]).replace("الحلقة","").replace("الأخيرة","").strip().replace(f" {num}","").strip(),
                    url,
                    new_episode["image"],
                    num
                )
                found = Cache.LastAddedAnimes.getByVal(url)
                if found:
                    found.Add(num)
            next_url = ParserUtils.__find_itemlist_by_name(_main, "Next Episodes")["url"]
            _resp,_,_ = ParserUtils._fetch_and_format(next_url)
            _main = _resp["mainEntity"]["itemListElement"]  # list value
            next_url = ParserUtils.__find_itemlist_by_name(_main, "Next Episodes")["url"]
        for _last_anime in Cache.LastAddedAnimes.Results:
            if _last_anime.NumberOfEpisodes == -1:
                Cache.LastAddedAnimes.Remove(_last_anime)
        Cache.LastAddedAnimes.Results = Cache.LastAddedAnimes.Results[:Config.MAX_RESULT] 
        Cache.LastAddedEpisodes.Results = Cache.LastAddedEpisodes.Results[:Config.MAX_RESULT] 
        return Cache.LastAddedAnimes,Cache.LastAddedEpisodes
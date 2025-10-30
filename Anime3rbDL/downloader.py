import hashlib
import os
import re
import random
import concurrent.futures
import time
from cloudscraper import create_scraper as HTTPSession
import urllib.parse
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn

from Anime3rbDL.enums import ResoultionData, ResponseFileInfo
from Anime3rbDL.exceptions import InvalidResponseError
from Anime3rbDL.config import Config

class _ServerFileHelper:
    """Helper class to parse and extract file information from HTTP response headers.

    Processes response headers to determine filename, content length, type, ETag,
    and range request support. Sanitizes filenames for safe filesystem use.

    Attributes:
        df (str): Default filename fallback.
        ds (int): Default size fallback.
        dt (str): Default content type fallback.
        status_code (int): HTTP status code from response.
        headers (dict): Lowercased response headers.
    """

    def __init__(self, response, df, ds=0, dt="video/mp4"):
        """Initialize the helper with response and fallback values.

        Args:
            response: HTTP response object with headers.
            df (str): Default filename if not in headers.
            ds (int, optional): Default file size. Defaults to 0.
            dt (str, optional): Default content type. Defaults to "video/mp4".
        """
        self.df = df
        self.ds = ds
        self.dt = dt
        headers = response.headers
        self.status_code = response.status_code
        self.headers = {k.lower(): v for k, v in headers.items()}
        if Config.LoggerV:
            Config.logger.debug(f"Parsed response headers for file: status={self.status_code}, content-length={self.headers.get('content-length')}")

    @property
    def info(self):
        """Extract structured file information from headers.

        Returns:
            ResponseFileInfo: Named tuple with filename, size, type, ETag, and range support.
        """
        file_info = ResponseFileInfo(
            self._parse_filename(),
            int(self.headers.get("content-length", self.ds)),
            self.headers.get("content-type", self.dt).split("/")[-1],
            self.headers.get("etag"),
            self.status_code == 206 and self.headers.get("accept-ranges") == "bytes",
        )
        if Config.LoggerV:
            Config.logger.debug(f"Extracted file info: {file_info.filename}, size={file_info.filesize}, type={file_info.fileext}, range_support={file_info.range_support}")
        return file_info

    def _parse_filename(self) -> str:
        """Extract and sanitize filename from Content-Disposition header.

        Uses regex to find filename in header, unquotes it, and applies cleaning rules
        for invalid characters, duplicates, and spacing. Falls back to default filename.

        Returns:
            str: Cleaned filename safe for filesystem use.
        """
        filename = None
        cd = self.headers.get("content-disposition")
        if cd:
            match = re.search(r'filename\*?="?([^"]+)"?', cd, flags=re.IGNORECASE)
            if match:
                filename = match.group(1)
        filename = filename or self.df
        filename = urllib.parse.unquote(filename)
        replacements = [
            (r'[<>:"/\\|?*]', "_"),  # Windows illegal chars
            (r"[-_]{2,}", "-"),  # collapse multiple - or _
            (r"[~]+", " "),  # replace ~ with space
            (r"\s*-\s*", " - "),  # normalize spacing around dashes
            (r"\s+", " "),  # collapse multiple spaces
        ]
        for pattern, repl in replacements:
            filename = re.sub(pattern, repl, filename)
        cleaned_filename = filename.rstrip(". ")
        if Config.LoggerV:
            Config.logger.debug(f"Sanitized filename: {cleaned_filename}")
        return cleaned_filename

class _FileValidate:
    """Validates partial downloads by comparing file samples with server content.

    Uses SHA-256 hashing of sampled chunks from local file and server to verify integrity.
    Samples from start, middle, end, and random positions to detect corruption.

    Attributes:
        get_req: Function to make range requests to server.
        sample_chunks (int): Size of each sample chunk.
        random_places (int): Number of random sample positions.
    """

    def __init__(self, get_req):
        """Initialize validator with request function and sample config.

        Args:
            get_req: Callable that performs HTTP range requests.
        """
        self.get_req = get_req
        self.sample_chunks = Config.SampleTestFileChunk
        self.random_places = random.randint(1, 5)
        if Config.LoggerV:
            Config.logger.debug(f"File validator initialized: sample_size={self.sample_chunks}, random_samples={self.random_places}")

    def validate(self, exist_size: int, file_path: str) -> bool:
        """Validate if local file matches server content up to exist_size.

        Checks minimum size, picks positions, samples local file and server,
        and compares hashes. Returns False on mismatch or errors.

        Args:
            exist_size (int): Current size of local file.
            file_path (str): Path to local file.

        Returns:
            bool: True if samples match (file valid), False otherwise.
        """
        try:
            min_chunks = (3 + self.random_places) * self.sample_chunks
            if exist_size < min_chunks:
                if Config.LoggerV:
                    Config.logger.debug(f"File too small for validation: {exist_size} < {min_chunks}")
                return False
            positions = self.__pick_positions(exist_size)
            if Config.LoggerV:
                Config.logger.debug(f"Validating {file_path} with positions: {positions}")
            local_hash = self.__get_file_samples(file_path, positions)
            server_hash = self.__get_server_samples(positions, exist_size)
            is_valid = local_hash == server_hash
            if Config.LoggerV:
                Config.logger.debug(f"Validation result for {file_path}: {'valid' if is_valid else 'invalid'} (local_hash={local_hash[:8]}..., server_hash={server_hash[:8]}...)")
            return is_valid
        except Exception as e:
            if Config.LoggerV:
                Config.logger.error(f"Validation failed for {file_path}: {e}")
            return False

    def __hash_data(self, data: bytes) -> str:
        """Compute SHA-256 hash of data as hex string.

        Args:
            data (bytes): Data to hash.

        Returns:
            str: Hex digest of the hash.
        """
        return hashlib.sha256(data).hexdigest()

    def __pick_positions(self, size: int):
        """Select sample positions: start, middle, end, and random points.

        Ensures positions avoid edges to prevent overlap issues.

        Args:
            size (int): Total file size.

        Returns:
            list[int]: List of byte positions for sampling.
        """
        positions = [
            0,                         # start
            size // 2,                 # middle
            size - self.sample_chunks  # end
        ]

        # Add N random positions avoiding overlap
        for _ in range(self.random_places):
            positions.append(random.randint(self.sample_chunks, size - self.sample_chunks * 2))

        return sorted(positions)  # Sort for consistent sampling

    def __get_file_samples(self, file_path: str, positions) -> str:
        """Read sample chunks from local file at given positions.

        Args:
            file_path (str): Path to file.
            positions (list[int]): Byte positions to sample.

        Returns:
            str: Combined hash of all samples.
        """
        samples = b""
        with open(file_path, "rb") as f:
            for pos in positions:
                f.seek(pos)
                samples += f.read(self.sample_chunks)
        return self.__hash_data(samples)

    def __get_server_samples(self, positions, size: int) -> str:
        """Fetch sample chunks from server using range requests.

        Args:
            positions (list[int]): Byte positions to sample.
            size (int): Total file size.

        Returns:
            str: Combined hash of server samples.
        """
        samples = b""
        for pos in positions:
            end = min(pos + self.sample_chunks - 1, size - 1)
            range_header = {"Range": f"bytes={pos}-{end}"}
            resp = self.get_req(range_header)
            if resp.status_code != 206:
                raise InvalidResponseError(f"Server range request failed: {resp.status_code}")
            samples += resp.content
        return self.__hash_data(samples)


class Downloader:
    """Main downloader class handling single and multi-threaded file downloads.

    Supports resume, validation, and fallback from multi-thread to single-thread.
    Uses cloudscraper for HTTP requests and rich for progress bars.

    Note on Multithreading Limitations:
        Multithreading may fail due to server-side restrictions:
        - Rate limiting: Too many concurrent requests trigger 429 errors.
        - Anti-bot measures: Cloudflare or similar protections block parallel requests from the same IP/session, resulting in 403 Forbidden or incomplete responses.
        - Session affinity: Servers may not handle concurrent range requests properly for the same file.
        In such cases, the downloader automatically falls back to single-threaded mode for reliability.

    Attributes:
        client: HTTP session (cloudscraper instance).
        timeout (int): Request timeout in seconds.
        chunk_size (int): Size of download chunks.
        workers (int): Maximum concurrent threads.
        sample_chunks (int): Size for validation samples.
        validator (_FileValidate): Instance for file integrity checks.
        url (str): Current download URL.
    """

    def __init__(
        self,
        client=HTTPSession()
    ):
        """Initialize downloader with HTTP client and config values.

        Args:
            client: HTTP session for requests. Defaults to cloudscraper.
        """
        self.client = client
        self.timeout = Config.timeout
        self.chunk_size = Config.DownloadChunks
        self.workers = max(1, Config.MaxWorkers)
        self.sample_chunks = Config.SampleTestFileChunk
        self.validator = _FileValidate(self.___get_content)
        self.url = None
        if Config.LoggerV:
            Config.logger.debug(f"Downloader initialized: timeout={self.timeout}s, chunk_size={self.chunk_size}, workers={self.workers}")

    def download(self, data: ResoultionData, output_dir: str = "."):
        """Download a file from URL, supporting resume and multi-threading.

        Checks for existing file and resumes if valid. Determines range support
        and chooses single or multi-thread mode. Falls back on errors.

        Args:
            data (ResoultionData): Download data with URL, filename, size.
            output_dir (str, optional): Directory to save file. Defaults to ".".

        Returns:
            str: Path to downloaded file.

        Raises:
            InvalidResponseError: If download fails critically.
        """
        url = data.DirectLink
        filename = data.FileName
        size = data.Size
        self.url = url
        os.makedirs(output_dir, exist_ok=True)
        if Config.LoggerV:
            Config.logger.debug(f"Starting download for {filename}: URL={url}, size={size}, output={output_dir}")

        try:
            resp = self.client.head(url, timeout=self.timeout)
            downloader = _ServerFileHelper(resp, filename, size)
        except Exception as e:
            if Config.LoggerV:
                Config.logger.warning(f"HEAD request failed: {e}, using range request fallback")
            downloader = _ServerFileHelper(self.___get_content(headers={"Range": "bytes=0-1"}), filename, size)
        file_info = downloader.info
        file_path = os.path.join(output_dir, file_info.filename)

        if os.path.exists(file_path) and self.resume(downloader, file_path, file_info):
            if Config.LoggerV:
                Config.logger.info(f"Download skipped (resume successful): {file_path}")
            return file_path

        range_support = self._check_range_support(url)
        if size == 0 or not range_support:
            if Config.LoggerV:
                Config.logger.info(f"Using single-thread download (no range support or zero size) for {file_path} (size={size})")
            return self._download_single(url, file_path, size)

        try:
            if Config.LoggerV:
                Config.logger.info(f"Attempting multithread download for {file_path} (size={file_info.filesize}) with {self.workers} workers")
            return self._download_multithread(url, file_path, file_info.filesize)
        except Exception as e:
            if Config.LoggerV:
                Config.logger.warning(f"Multithread download failed for {file_path}: {e}. Falling back to single-thread mode.")
            return self._download_single(url, file_path, file_info.filesize)

    def resume(self, downloader, file_path, file_info):
        """Resume a partial download if valid and server supports ranges.

        Validates existing file, checks if complete, and resumes either multi or single-thread.
        Falls back to single-thread if multi fails.

        Args:
            downloader (_ServerFileHelper): Helper with response info.
            file_path (str): Path to partial file.
            file_info (ResponseFileInfo): File metadata.

        Returns:
            bool: True if resume successful or file complete, False otherwise.
        """
        if not os.path.exists(file_path):
            if Config.LoggerV:
                Config.logger.debug(f"File does not exist for resume: {file_path}")
            return False
        exist_size = os.path.getsize(file_path)
        is_validate = self.validator.validate(exist_size, file_path)
        if not is_validate:
            if Config.LoggerV:
                Config.logger.warning(f"Validation failed for partial file {file_path} (size={exist_size}), redownloading")
            return False
        if exist_size == file_info.filesize:
            Config.logger.info(f"File already fully downloaded and valid: {file_path} (size={exist_size})")
            return True
        remaining_size = file_info.filesize - exist_size
        Config.logger.info(f"Resuming valid partial download: {exist_size}/{file_info.filesize} bytes ({remaining_size} remaining) for {file_path}")

        # Check if multithread resume is feasible
        range_support = self._check_range_support(self.url)
        if self.workers > 1 and remaining_size > self.workers * self.chunk_size and range_support:
            Config.logger.info(f"Attempting multithread resume for {file_path} with {self.workers} workers (remaining={remaining_size})")
            try:
                return self._resume_multithread(file_path, file_info, exist_size, remaining_size)
            except Exception as e:
                Config.logger.warning(f"Multithread resume failed for {file_path}: {e}, falling back to single-thread resume")

        # Resume append single thread
        Config.logger.info(f"Resuming single-thread download from byte {exist_size} for {file_path}")
        try:
            with self.client.get(self.url, headers={"Range": f"bytes={exist_size}-"}, stream=True, timeout=self.timeout) as r:
                if r.status_code != 206:
                    Config.logger.warning(f"Server rejected resume request (status={r.status_code}) for {file_path}")
                    return False
                with open(file_path, "ab") as f, Progress(
                    TextColumn("[cyan]{task.fields[filename]}", justify="right"),
                    BarColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task("resume", filename=os.path.basename(file_path), total=file_info.filesize, completed=exist_size)
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, advance=len(chunk))
                    if Config.LoggerV:
                        Config.logger.debug(f"Single-thread resume downloaded {downloaded} bytes for {file_path}")
            final_size = os.path.getsize(file_path)
            if final_size == file_info.filesize:
                Config.logger.info(f"Single-thread resume completed successfully: {file_path}")
                return True
            else:
                Config.logger.error(f"Resume incomplete: expected {file_info.filesize}, got {final_size}")
                return False
        except Exception as e:
            Config.logger.error(f"Single-thread resume failed for {file_path}: {e}")
            return False

    def _check_range_support(self, url: str) -> bool:
        """Test if server supports HTTP range requests for partial downloads.

        Performs HEAD and a small range GET to verify Accept-Ranges and 206 status.

        Args:
            url (str): URL to test.

        Returns:
            bool: True if range requests are supported.
        """
        try:
            resp = self.client.head(url, timeout=self.timeout)
            if Config.LoggerV:
                Config.logger.debug(f"HEAD response for range check: status={resp.status_code}, accept-ranges={resp.headers.get('accept-ranges')}")
        except Exception as e:
            if Config.LoggerV:
                Config.logger.debug(f"HEAD request failed for range check: {e}")
            return False
        if resp.headers.get("Accept-Ranges", "none").lower() != "bytes":
            if Config.LoggerV:
                Config.logger.debug("Server does not advertise byte-range support")
            return False
        try:
            test_resp = self.client.get(url, headers={"Range": "bytes=0-1"}, timeout=self.timeout)
            range_supported = test_resp.status_code == 206
            if Config.LoggerV:
                Config.logger.debug(f"Range test result: status={test_resp.status_code}, supported={range_supported}")
            return range_supported
        except Exception as e:
            if Config.LoggerV:
                Config.logger.debug(f"Range test request failed: {e}")
            return False

    def _download_single(self, url: str, file_path: str, size: int = 0) -> str:
        """Perform single-threaded download with progress tracking.

        Downloads entire file sequentially, writing chunks to disk.

        Args:
            url (str): Download URL.
            file_path (str): Output file path.
            size (int, optional): Expected file size. Defaults to 0.

        Returns:
            str: Path to downloaded file.

        Raises:
            InvalidResponseError: If HTTP request fails.
        """
        Config.logger.info(f"Starting single-thread download: {file_path} (expected size={size})")
        try:
            with self.client.get(url, stream=True, timeout=self.timeout) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", size))
                if Config.LoggerV:
                    Config.logger.debug(f"Single-thread download headers: content-length={total}, status={r.status_code}")
                with open(file_path, "wb") as f, Progress(
                    TextColumn("[cyan]{task.fields[filename]}", justify="right"),
                    BarColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task("download", filename=os.path.basename(file_path), total=total)
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, advance=len(chunk))
                    if Config.LoggerV:
                        Config.logger.debug(f"Single-thread download wrote {downloaded} bytes to {file_path}")
            final_size = os.path.getsize(file_path)
            Config.logger.info(f"Single-thread download completed: {file_path} (final size={final_size})")
            return file_path
        except Exception as e:
            Config.logger.error(f"Single-thread download failed for {file_path}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up partial file
            raise InvalidResponseError(f"Single-thread download failed: {e}")

    def _fetch_range(self, url, start, end, idx):
        """Fetch a byte range from URL in a thread-safe manner.

        Used by multi-thread downloader.

        Args:
            url (str): Download URL.
            start (int): Start byte.
            end (int): End byte.
            idx (int): Range index.

        Returns:
            tuple: (index, content bytes).

        Raises:
            InvalidResponseError: If range request fails.
        """
        headers = {"Range": f"bytes={start}-{end}"}
        resp = self.client.get(url, headers=headers, timeout=self.timeout, stream=True)
        if resp.status_code == 206:
            content = b"".join(chunk for chunk in resp.iter_content(chunk_size=self.chunk_size))
            if Config.LoggerV:
                Config.logger.debug(f"Range {idx} fetched: bytes {start}-{end} ({len(content)} bytes)")
            return idx, content
        else:
            raise InvalidResponseError(f"Range request {start}-{end} failed: status={resp.status_code}")

    def _download_multithread(self, url: str, file_path: str, size: int) -> str:
        """Download file using multiple threads for parallel range requests.

        Divides file into worker-sized parts, fetches concurrently with delays
        to avoid rate limits, assembles parts, and updates progress.

        Args:
            url (str): Download URL.
            file_path (str): Output file path.
            size (int): Total file size.

        Returns:
            str: Path to assembled file.

        Raises:
            InvalidResponseError: If ranges fail or assembly errors.
        """
        Config.logger.info(f"Starting multithread download: {file_path} (size={size}) with {self.workers} workers")
        if size <= 0:
            raise InvalidResponseError("Cannot multithread zero-size file")
        part_size = max(1, size // self.workers)
        ranges = [(i * part_size, min((i + 1) * part_size - 1, size - 1)) for i in range(self.workers)]
        if Config.LoggerV:
            Config.logger.debug(f"Multithread ranges: {ranges}")

        with Progress(
            TextColumn("[cyan]{task.fields[filename]}", justify="right"),
            BarColumn(),
            DownloadColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("download", filename=os.path.basename(file_path), total=size)
            parts = [None] * self.workers
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {}
                for idx, (start, end) in enumerate(ranges):
                    time.sleep(0.5 * idx)  # Stagger requests to mitigate rate limiting
                    future = executor.submit(self._fetch_range, url, start, end, idx)
                    futures[future] = idx
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]
                    try:
                        range_idx, data = future.result()
                        parts[range_idx] = data
                        progress.update(task, advance=len(data))
                        completed += 1
                        if Config.LoggerV:
                            Config.logger.debug(f"Completed range {range_idx}/{self.workers}: {len(data)} bytes")
                    except Exception as e:
                        Config.logger.error(f"Range {idx} failed in multithread: {e}")
                        raise
                if Config.LoggerV:
                    Config.logger.debug(f"All {completed} ranges completed for multithread download")

            try:
                with open(file_path, "wb") as f:
                    total_written = 0
                    for part in parts:
                        if part is None:
                            raise InvalidResponseError("Missing part in multithread assembly")
                        f.write(part)
                        total_written += len(part)
                    if Config.LoggerV:
                        Config.logger.debug(f"Assembled {total_written} bytes from {self.workers} parts")
            except Exception as e:
                Config.logger.error(f"Failed assembling multithread parts for {file_path}: {e}")
                raise InvalidResponseError(f"File assembly failed: {e}")

        final_size = os.path.getsize(file_path)
        Config.logger.info(f"Multithread download completed: {file_path} (final size={final_size})")
        return file_path

    def _resume_multithread(self, file_path: str, file_info, exist_size: int, remaining_size: int) -> bool:
        """Resume download using multiple threads for remaining file parts.

        Similar to _download_multithread but appends to existing file from exist_size.
        Validates final size after assembly.

        Args:
            file_path (str): Path to partial file.
            file_info (ResponseFileInfo): File metadata.
            exist_size (int): Bytes already downloaded.
            remaining_size (int): Bytes left to download.

        Returns:
            bool: True if resume completes successfully, False if incomplete.

        Raises:
            InvalidResponseError: If range fetches or append fail.
        """
        Config.logger.info(f"Starting multithread resume: {file_path} (remaining={remaining_size}) with {self.workers} workers")
        part_size = max(1, remaining_size // self.workers)
        ranges = [(exist_size + i * part_size, min(exist_size + (i + 1) * part_size - 1, file_info.filesize - 1)) for i in range(self.workers)]
        if Config.LoggerV:
            Config.logger.debug(f"Multithread resume ranges: {ranges}")

        with Progress(
            TextColumn("[cyan]{task.fields[filename]}", justify="right"),
            BarColumn(),
            DownloadColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("resume", filename=os.path.basename(file_path), total=file_info.filesize, completed=exist_size)
            parts = [None] * self.workers
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {}
                for idx, (start, end) in enumerate(ranges):
                    time.sleep(0.5 * idx)  # Stagger to avoid rate limits
                    future = executor.submit(self._fetch_range, self.url, start, end, idx)
                    futures[future] = idx
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]
                    try:
                        range_idx, data = future.result()
                        parts[range_idx] = data
                        progress.update(task, advance=len(data))
                        completed += 1
                        if Config.LoggerV:
                            Config.logger.debug(f"Resume range {range_idx} completed: {len(data)} bytes")
                    except Exception as e:
                        Config.logger.error(f"Resume range {idx} failed: {e}")
                        raise
                if Config.LoggerV:
                    Config.logger.debug(f"All {completed} resume ranges completed")

            try:
                with open(file_path, "ab") as f:
                    total_appended = 0
                    for part in parts:
                        if part is None:
                            raise InvalidResponseError("Missing resume part")
                        f.write(part)
                        total_appended += len(part)
                    if Config.LoggerV:
                        Config.logger.debug(f"Appended {total_appended} bytes from {self.workers} resume parts")
            except Exception as e:
                Config.logger.error(f"Failed appending multithread resume parts to {file_path}: {e}")
                raise InvalidResponseError(f"Resume append failed: {e}")

        final_size = os.path.getsize(file_path)
        if final_size == file_info.filesize:
            Config.logger.info(f"Multithread resume completed successfully: {file_path} (final size={final_size})")
            return True
        else:
            Config.logger.warning(f"Multithread resume incomplete: expected {file_info.filesize}, got {final_size}")
            return False

    def ___get_content(self, headers={}):
        """Get HTTP response for current URL with optional headers.

        Used internally for range requests and validation.

        Args:
            headers (dict, optional): Additional headers. Defaults to {}.

        Returns:
            Response: HTTP response object.

        Raises:
            InvalidResponseError: If status is not 200 or 206.
        """
        _response = self.client.get(self.url, headers=headers, stream=True, timeout=self.timeout)
        if _response.status_code not in (200, 206):
            raise InvalidResponseError(f"Invalid response status: {_response.status_code}")
        if Config.LoggerV:
            Config.logger.debug(f"___get_content response: status={_response.status_code}, headers={dict(_response.headers)}")
        return _response

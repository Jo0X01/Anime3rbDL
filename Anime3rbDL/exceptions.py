"""
exceptions.py

Custom exception classes for Anime3rbDL.

These exceptions allow Anime3rbDL to fail gracefully without abruptly
terminating the host process. The CLI entry point can catch these
and decide whether to exit, retry, or show a friendly error.
"""


class Anime3rbDLError(Exception):
    """Base exception for all Anime3rbDL exceptions."""


# ---------------- Configuration Errors ---------------- #

class ConfigError(Anime3rbDLError):
    """Raised for configuration-related issues (e.g., invalid settings)."""


class AuthenticationError(ConfigError):
    """Raised when login or registration fails."""


class ProxyError(ConfigError):
    """Raised when proxy settings are invalid or unreachable."""


class TimeoutError(ConfigError):
    """Raised when a network request exceeds the allowed timeout."""


# ---------------- Search & Parsing Errors ---------------- #

class SearchError(Anime3rbDLError):
    """Raised for errors during search queries or parsing search results."""


class ParseError(Anime3rbDLError):
    """Raised when HTML or JSON parsing fails."""


class NotFoundError(SearchError):
    """Raised when no results are found or requested item is missing."""


# ---------------- Anime & Episode Errors ---------------- #

class AnimeNotFoundError(NotFoundError):
    """Raised when the requested anime cannot be found."""


class EpisodeNotFoundError(NotFoundError):
    """Raised when the requested episode cannot be found."""


class InvalidResolutionError(Anime3rbDLError):
    """Raised when an unsupported or invalid video resolution is requested."""


class DownloadError(Anime3rbDLError):
    """Raised for errors during download (e.g., broken links, failed chunks)."""


# ---------------- Cache & State Errors ---------------- #

class CacheError(Anime3rbDLError):
    """Raised when cached data is invalid or inconsistent."""


class StateError(Anime3rbDLError):
    """Raised when the application is in an unexpected state."""


# ---------------- Download Errors ---------------- #

class DownloadError(Exception):
    """Base class for download-related errors."""


class NetworkError(DownloadError):
    """Raised when a network request fails."""


class InvalidResponseError(DownloadError):
    """Raised when the server response is invalid (e.g., 4xx/5xx)."""


class RangeNotSupportedError(DownloadError):
    """Raised when the server does not support HTTP Range requests."""


class ResumeNotSupportedError(DownloadError):
    """Raised when resume is not supported but requested."""


class FileWriteError(DownloadError):
    """Raised when writing to the file system fails."""

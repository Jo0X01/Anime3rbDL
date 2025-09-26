"""
Custom logger for Anime3rbDL with verbose support.

This module provides a custom logging implementation using Python's standard
logging module. It supports verbose mode, file logging, console output
with colors, and maintains compatibility with the existing logging interface.
"""

import logging
import sys
import os
from typing import Optional

from Anime3rbDL.config import Config


class CallerFormatter(logging.Formatter):
    """Custom formatter that captures caller's function and line number."""

    def format(self, record):
        # Get caller's frame, skipping logging-related frames
        import inspect
        frame = inspect.currentframe().f_back
        while frame:
            filename = frame.f_code.co_filename
            if 'logging' not in filename and 'logger.py' not in filename:
                break
            frame = frame.f_back
        if frame:
            record.funcName = frame.f_code.co_name
            record.lineno = frame.f_lineno
            record.module = frame.f_globals['__name__']
            # Get class name if it's a method
            class_name = ''
            if 'self' in frame.f_locals:
                self_obj = frame.f_locals['self']
                class_name = self_obj.__class__.__name__
            record.caller_info = f"{record.module}.{class_name}.{record.funcName}" if class_name else f"{record.module}.{record.funcName}"
        else:
            record.caller_info = "unknown"
        return super().format(record)


class ColoredFormatter(CallerFormatter):
    """Custom formatter with ANSI color codes for console output."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def __init__(self, fmt=None, datefmt=None, style='%', use_colors=True):
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors and not Config.no_color

    def format(self, record):
        # Get caller's info first
        super(ColoredFormatter, self).format(record)

        # Add color to level name if colors are enabled
        if self.use_colors and record.levelname in self.COLORS:
            colored_level = f"{self.COLORS[record.levelname]}[{record.levelname}]{self.COLORS['RESET']}"
            record.levelname = colored_level
        else:
            record.levelname = f"[{record.levelname}]"

        return super(ColoredFormatter, self).format(record)


class Anime3rbLogger:
    """
    Custom logger for Anime3rbDL with verbose and file logging support.

    This logger provides a drop-in replacement for the previous loguru-based logger,
    maintaining the same interface while using Python's standard logging module.
    It supports verbose mode, file output, console output with colors, and level filtering.

    Attributes:
        logger (logging.Logger): The underlying Python logger instance.
        verbose (bool): Whether verbose (debug) logging is enabled.
        log_file (str): Path to log file, or None for console-only.
        level (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
    """

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None, level: str = "INFO"):
        """
        Initialize the custom logger.

        Args:
            verbose (bool): Enable verbose (debug) logging.
            log_file (str): Path to log file. If None, logs to console only.
            level (str): Base logging level.
        """
        self.verbose = verbose
        self.log_file = log_file
        self.level = level.upper()

        # Create logger
        self.logger = logging.getLogger('Anime3rbDL')
        self.logger.setLevel(logging.DEBUG)  # Always capture all levels, filter at handlers

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Set effective level
        effective_level = logging.DEBUG if self.verbose else getattr(logging, self.level, logging.INFO)

        # Filter function for suppressing warnings when no_warn is used
        def filter_msgs(record):
            if Config.no_warn and record.levelname == "WARNING":
                return False
            return True

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(effective_level)
        console_handler.addFilter(filter_msgs)

        if self.verbose:
            # Verbose format with timestamp, module, function, line
            console_format = (
                "\033[32m%(asctime)s\033[0m | "  # Green timestamp
                "%(levelname)s | "
                "\033[36m%(caller_info)s:%(lineno)d\033[0m | "  # Cyan location
                "%(message)s"
            )
        else:
            # Simple format
            console_format = "%(levelname)s %(message)s"

        console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S.%f'[:-3])
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if self.log_file and self.log_file.strip():
            # Create directory if needed
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(effective_level)
            file_handler.addFilter(filter_msgs)

            if self.verbose:
                file_format = (
                    "%(asctime)s | %(levelname)s | %(caller_info)s:%(lineno)d | %(message)s"
                )
            else:
                file_format = "%(asctime)s | %(levelname)s | %(message)s"

            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        if not Config.no_warn:
            self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log an exception message with traceback."""
        self.logger.exception(message, *args, **kwargs)

    def log(self, level: str, message: str, *args, **kwargs):
        """Log a message at the specified level."""
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message, *args, **kwargs)

    def set_level(self, level: str):
        """Update the logging level for all handlers."""
        effective_level = getattr(logging, level.upper(), logging.INFO)
        self.level = level.upper()

        # Filter function for suppressing warnings when no_warn is used
        def filter_msgs(record):
            if Config.no_warn and record.levelname == "WARNING":
                return False
            return True

        for handler in self.logger.handlers:
            handler.setLevel(effective_level)
            handler.addFilter(filter_msgs)

    def enable_verbose(self):
        """Enable verbose (debug) logging."""
        self.verbose = True
        for handler in self.logger.handlers:
            handler.setLevel(logging.DEBUG)

    def disable_verbose(self):
        """Disable verbose logging, revert to base level."""
        self.verbose = False
        effective_level = getattr(logging, self.level, logging.INFO)
        for handler in self.logger.handlers:
            handler.setLevel(effective_level)


# Global logger instance
_logger_instance = None


def get_logger(verbose: bool = False, log_file: Optional[str] = None, level: str = "INFO") -> Anime3rbLogger:
    """
    Get or create the global logger instance.

    Args:
        verbose (bool): Enable verbose logging.
        log_file (str): Path to log file.
        level (str): Logging level.

    Returns:
        Anime3rbLogger: The global logger instance.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Anime3rbLogger(verbose, log_file, level)
    else:
        # Update existing instance if parameters changed
        if _logger_instance.verbose != verbose:
            if verbose:
                _logger_instance.enable_verbose()
            else:
                _logger_instance.disable_verbose()
        if _logger_instance.log_file != log_file:
            # Reinitialize if log file changed (simplified, could be improved)
            _logger_instance = Anime3rbLogger(verbose, log_file, level)
        if _logger_instance.level != level.upper():
            _logger_instance.set_level(level)

    return _logger_instance

"""Structured logging for MLB Game Tracker.

This module provides a structured logging system that:
- Outputs to both console and file
- Supports log levels (DEBUG, INFO, WARNING, ERROR)
- Maintains backward compatibility with the original simple API
- Supports emoji stripping for plain text output

Use:
- info(...): Log informational messages (always visible)
- warn(...): Log warning messages (always visible)
- debug(...): Log debug messages (only when verbose=True)
- error(...): Log error messages (always visible)

Configuration:
- set_verbosity(True/False): Enable/disable debug output
- set_use_emoji(True/False): Enable/disable emoji in output
- configure_file_logging(path): Enable logging to a file
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Module-level state
VERBOSE: bool = False
USE_EMOJI: bool = True
_logger: Optional[logging.Logger] = None
_file_handler: Optional[logging.FileHandler] = None


class EmojiFilter(logging.Filter):
    """Filter that optionally strips emojis from log messages."""

    # Common emojis used in this project
    EMOJI_CHARS = "📄📊📂📦🆕🔄✅❌⚠️⚾️🗂️👥🏆🏟️📝🌐🎉🔍▶💾🗑️💡"

    def __init__(self, strip_emoji: bool = False):
        super().__init__()
        self.strip_emoji = strip_emoji

    def filter(self, record: logging.LogRecord) -> bool:
        if self.strip_emoji:
            record.msg = self._strip_emoji(str(record.msg))
        return True

    def _strip_emoji(self, msg: str) -> str:
        """Remove emoji characters from the beginning of a message."""
        return msg.lstrip(self.EMOJI_CHARS + " ")


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to console output."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        # Simple format for console - just the message
        if self.use_colors and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            return f"{color}{record.msg}{reset}"
        return record.msg


def _get_logger() -> logging.Logger:
    """Get or create the application logger."""
    global _logger

    if _logger is None:
        _logger = logging.getLogger("mlb_tracker")
        _logger.setLevel(logging.DEBUG)  # Capture all levels, filter at handler level

        # Console handler - simple output like original print()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter(use_colors=True))
        _logger.addHandler(console_handler)

        # Prevent propagation to root logger
        _logger.propagate = False

    return _logger


def set_verbosity(verbose: bool) -> None:
    """Enable or disable debug output."""
    global VERBOSE
    VERBOSE = bool(verbose)

    logger = _get_logger()
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.DEBUG if verbose else logging.INFO)


def set_use_emoji(use_emoji: bool) -> None:
    """Enable or disable emoji in output."""
    global USE_EMOJI
    USE_EMOJI = bool(use_emoji)

    logger = _get_logger()
    # Update emoji filter on all handlers
    for handler in logger.handlers:
        # Remove existing emoji filters
        handler.filters = [f for f in handler.filters if not isinstance(f, EmojiFilter)]
        # Add new filter
        handler.addFilter(EmojiFilter(strip_emoji=not use_emoji))


def configure_file_logging(
    log_path: Optional[str | Path] = None,
    log_level: int = logging.DEBUG
) -> Path:
    """Configure file-based logging.

    Args:
        log_path: Path to log file. If None, creates a timestamped log in the
                  project's logs directory.
        log_level: Minimum log level for file output (default: DEBUG)

    Returns:
        Path to the log file being used.
    """
    global _file_handler

    logger = _get_logger()

    # Remove existing file handler if any
    if _file_handler is not None:
        logger.removeHandler(_file_handler)
        _file_handler.close()

    # Determine log path
    if log_path is None:
        # Create logs directory in project root
        from .constants import BASE_DIR
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = logs_dir / f"mlb_tracker_{timestamp}.log"
    else:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create file handler with detailed format
    _file_handler = logging.FileHandler(log_path, encoding='utf-8')
    _file_handler.setLevel(log_level)

    # Detailed format for file logging
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    _file_handler.setFormatter(file_formatter)

    # Always strip emoji in file output for cleaner logs
    _file_handler.addFilter(EmojiFilter(strip_emoji=True))

    logger.addHandler(_file_handler)

    return log_path


def _format(msg: str) -> str:
    """Format message, optionally stripping emoji."""
    if USE_EMOJI:
        return msg
    return msg.lstrip("📄📊📂📦🆕🔄✅❌⚠️⚾️🗂️👥🏆🏟️📝🌐🎉🔍▶💾🗑️💡 ")


def info(msg: str) -> None:
    """Log an informational message."""
    _get_logger().info(_format(msg))


def warn(msg: str) -> None:
    """Log a warning message."""
    _get_logger().warning(_format(msg))


def debug(msg: str) -> None:
    """Log a debug message (only visible when verbose=True)."""
    if VERBOSE:
        _get_logger().debug(_format(msg))


def error(msg: str, exc_info: bool = False) -> None:
    """Log an error message.

    Args:
        msg: The error message
        exc_info: If True, include exception traceback in the log
    """
    _get_logger().error(_format(msg), exc_info=exc_info)

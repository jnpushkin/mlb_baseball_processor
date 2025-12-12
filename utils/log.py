"""Minimal logging helpers.

This project originally used a lot of direct `print()` calls (often with emojis).
To keep behavior stable while reducing noise, we centralize debug output behind a
single VERBOSE flag.

Use:
- info(...): always prints
- warn(...): always prints
- debug(...): prints only when VERBOSE is True

If you want full structured logging later, this module can be swapped to the
standard `logging` module without changing call sites.
"""

from __future__ import annotations

VERBOSE: bool = False
USE_EMOJI: bool = True


def set_verbosity(verbose: bool) -> None:
    global VERBOSE
    VERBOSE = bool(verbose)


def set_use_emoji(use_emoji: bool) -> None:
    global USE_EMOJI
    USE_EMOJI = bool(use_emoji)


def _format(msg: str) -> str:
    if USE_EMOJI:
        return msg
    # Strip out common leading emoji + whitespace.
    return msg.lstrip("📄📊📂📦🆕🔄✅❌⚠️⚾️🗂️👥🏆🏟️📝🌐🎉🔍▶ ")


def info(msg: str) -> None:
    print(_format(msg))


def warn(msg: str) -> None:
    print(_format(msg))


def debug(msg: str) -> None:
    if VERBOSE:
        print(_format(msg))

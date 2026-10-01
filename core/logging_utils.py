"""Small structured logger used across the pipeline (stdlib only)."""
from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False

# ANSI colours (auto-disabled when not a TTY / when NO_COLOR is set)
_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[36m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
}
_RESET = "\033[0m"


class _Formatter(logging.Formatter):
    def __init__(self, color: bool) -> None:
        super().__init__("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if self.color:
            c = _COLORS.get(record.levelname, "")
            return f"{c}{msg}{_RESET}"
        return msg


def setup_logging(level: str | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    handler = logging.StreamHandler(sys.stdout)
    color = sys.stdout.isatty() and not os.getenv("NO_COLOR")
    handler.setFormatter(_Formatter(color))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, lvl, logging.INFO))
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)

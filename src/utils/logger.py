"""
src/utils/logger.py
Centralised Loguru logger configuration for the AeroMind AI pipeline.

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Ready.")

All modules should use this instead of importing loguru directly,
so that log level and format can be controlled from config in one place.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _root_logger


# ─── Module-level cache ───────────────────────────────────────────────────────
_configured = False


def configure_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Configure the root Loguru logger.
    Call once at application startup (e.g. in main scripts).

    Args:
        level:           Minimum log level: DEBUG | INFO | WARNING | ERROR | SUCCESS
        log_dir:         Directory to write rotating log files (None → no file sink)
        enable_console:  Write to stderr with colour
        enable_file:     Write to rotating file in log_dir
    """
    global _configured

    # Remove default handler
    _root_logger.remove()

    fmt_console = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    )
    fmt_file = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} — {message}"
    )

    if enable_console:
        _root_logger.add(
            sys.stderr,
            format=fmt_console,
            level=level,
            colorize=True,
            enqueue=True,
        )

    if enable_file and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        _root_logger.add(
            str(log_path / "pipeline_{time:YYYY-MM-DD}.log"),
            format=fmt_file,
            level="DEBUG",          # always capture DEBUG in file
            rotation="50 MB",
            retention="14 days",
            compression="gz",
            enqueue=True,
        )

    _configured = True


def configure_from_cfg(cfg: dict) -> None:
    """
    Configure logging directly from the project config dictionary.

    Args:
        cfg: Full config dict containing cfg['logging'] section.
    """
    log_cfg = cfg.get("logging", {})
    configure_logging(
        level=log_cfg.get("level", "INFO"),
        log_dir=log_cfg.get("log_dir"),
        enable_console=True,
        enable_file=log_cfg.get("log_to_file", True),
    )


def get_logger(name: str = "aic4"):
    """
    Return the configured Loguru logger.
    If not yet configured, sets up with sensible defaults.

    Args:
        name: Module name (for display only — Loguru is a global singleton)
    """
    global _configured
    if not _configured:
        configure_logging()
    return _root_logger.bind(module=name)


# ─── Convenience export ───────────────────────────────────────────────────────
logger = _root_logger

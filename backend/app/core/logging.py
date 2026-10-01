"""Central logging configuration for JalRakshak-HD.

Supports console and file handlers with structured format, timestamps,
log levels, and originating module names.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


DEFAULT_LOG_DIR = Path(r"C:\JalRakshak-HD\logs")
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "jalrakshak.log"
LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "jalrakshak",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure and return a structured logger for console and file output.

    Parameters
    ----------
    name : str
        The module/logger name.
    log_file : Optional[Path]
        Target log file path. Defaults to C:\\JalRakshak-HD\\logs\\jalrakshak.log.
    level : int
        Logging level (e.g. logging.INFO, logging.DEBUG).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    target_file = log_file or DEFAULT_LOG_FILE
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(target_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        console_handler.setLevel(logging.WARNING)
        logger.warning(f"Could not initialize file logger at {target_file}: {e}")

    return logger


# Default application-wide root logger instance
logger = setup_logger()

from __future__ import annotations
import logging
from queue import Queue
from logging import Logger
from logging.handlers import TimedRotatingFileHandler, QueueHandler
import os
from pathlib import Path
from typing import Any
from .constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOGGING_FORMATTER,
    YYMMDD_FORMAT,
    HHMMSS_COLON_FORMAT,
    LOG_FILE,
    LOG_INTERVAL,
    LOGS_DIR,
    LOGGING_FORMAT,
    BACKUP_FILES_COUNT,
)


def configure_root_logger(
    log_queue: Queue[Any] | None = None,
    logger_name: str = "__root__",
    logger_base_path: str | None = None,
) -> Logger:
    """Configure the root logger, optionally using a QueueHandler."""
    logging.basicConfig(level=logging.DEBUG)
    logger: Logger = logging.getLogger(logger_name)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    if logger_base_path is None:
        logger_base_path = os.getcwd()

    date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

    formatter = logging.Formatter(fmt=LOGGING_FORMAT, datefmt=date_fmt)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    if log_queue:
        handler = QueueHandler(log_queue)
    else:
        Path(f"{logger_base_path}/{LOGS_DIR}").mkdir(exist_ok=True, parents=True)
        filename = Path(f"{logger_base_path}/{LOGS_DIR}/{LOG_FILE}")

        handler = TimedRotatingFileHandler(
            filename=filename, when=LOG_INTERVAL, backupCount=BACKUP_FILES_COUNT
        )
        handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Suppress DEBUG logs from urllib3
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.INFO)

    return logger


def configure_child_logger(logger_name: str, logger: Logger | None):

    if logger is None:
        logger = logging.getLogger(logger_name)
        logger.setLevel(DEFAULT_LOG_LEVEL)
    
    if not logger.hasHandlers():
        _log_handler = logging.StreamHandler()

        _log_handler.setFormatter(DEFAULT_LOGGING_FORMATTER)
        logger.addHandler(_log_handler)
    
    # Suppress DEBUG logs from urllib3
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.INFO)
    
    return logger
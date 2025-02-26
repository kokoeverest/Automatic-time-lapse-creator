from __future__ import annotations
from logging import Logger, LogRecord
from queue import Queue

def configure_root_logger(
    log_queue: Queue[str | LogRecord] | None = ...,
    logger_base_path: str | None = ...,
    logger_name: str = ...,
) -> Logger: ...

def configure_child_logger(logger_name: str, logger: Logger | None) -> Logger: ...
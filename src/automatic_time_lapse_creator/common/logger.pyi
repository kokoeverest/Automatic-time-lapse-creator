from __future__ import annotations
from logging import Logger, LogRecord
from queue import Queue

def configure_logger(
    log_queue: Queue[str | LogRecord] | None = ...,
    logger_base_path: str | None = ...,
    logger_name: str = ...,
) -> Logger: ...

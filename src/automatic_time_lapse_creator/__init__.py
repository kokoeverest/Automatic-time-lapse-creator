import logging
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from .common.constants import (
    YYMMDD_FORMAT,
    HHMMSS_COLON_FORMAT,
    LOG_FILE,
    LOG_INTERVAL,
    LOGS_DIR,
    LOGGING_FORMAT,
    BACKUP_FILES_COUNT
)

logger: Logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)
cwd = os.getcwd()
Path(f"{cwd}/{LOGS_DIR}").mkdir(exist_ok=True)
filename = Path(f"{cwd}/{LOGS_DIR}/{LOG_FILE}")
date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

file_handler = TimedRotatingFileHandler(
    filename=filename, when=LOG_INTERVAL, backupCount=BACKUP_FILES_COUNT
)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(fmt=LOGGING_FORMAT, datefmt=date_fmt)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress DEBUG logs from urllib3
urllib3_logger = logging.getLogger("urllib3")
urllib3_logger.setLevel(logging.INFO)
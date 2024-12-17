import pickle
from pathlib import Path
import logging
from datetime import datetime as dt
import os
from .common.constants import (
    LOGS_DIR,
    YYMMDD_FORMAT,
    LOG_FILE,
    LOGGING_FORMAT,
    HHMMSS_COLON_FORMAT,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
cwd = os.getcwd()
Path(f"{cwd}{LOGS_DIR}").mkdir(exist_ok=True)
filename = Path(f"{cwd}{LOGS_DIR}/{dt.now().strftime(YYMMDD_FORMAT)}{LOG_FILE}")
date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

logging.basicConfig(filename=filename, datefmt=date_fmt, format=LOGGING_FORMAT)


class CacheManager:
    """Class for managing the state of TimeLapseCreator objects. State of the object
    is saved (pickled) in a file and the filename has a prefix *cache_* and ends with
    the *location_name* attribute of the TimeLapseCreator"""

    @classmethod
    def write(cls, time_lapse_creator: object, location: str, path_prefix: str) -> None:
        """Writes the TimeLapseCreator object to a file, overwriting existing objects
        if the file already exists"""
        current_path = Path(f"{path_prefix}/cache/cache_{location}.p")
        current_path.parent.mkdir(parents=True, exist_ok=True)
        with current_path.open("wb") as file:
            pickle.dump(time_lapse_creator, file)
        logger.info(f"State cached in {current_path}")

    @classmethod
    def get(cls, location: str, path_prefix: str) -> object:
        """Retrieves the pickled object in the file. If the file is empty or if it is not found
        it will return an Exception"""
        current_path = Path(f"{path_prefix}/cache/cache_{location}.p")
        logger.info(f"Getting state from  {current_path}")
        with current_path.open("rb") as file:
            return pickle.load(file)

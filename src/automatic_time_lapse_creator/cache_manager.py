import pickle
from pathlib import Path
import logging
import os
from .common.constants import CACHE_DIR, CACHE_FILE_PREFIX, PICKLE_FILE
from .common.utils import shorten




class CacheManager:
    """Class for managing the state of TimeLapseCreator objects. State of the object
    is saved (pickled) in a file and the filename has a prefix *cache_* and ends with
    the *location_name* attribute of the TimeLapseCreator"""

    @staticmethod
    def write(
        logger: logging.Logger,
        time_lapse_creator: object,
        location: str,
        path_prefix: str,
        quiet: bool = True,
    ) -> None:
        """Writes the TimeLapseCreator object to a file, overwriting existing objects
        if the file already exists"""
        current_path = Path(
            f"{path_prefix}/{CACHE_DIR}/{CACHE_FILE_PREFIX}{location}{PICKLE_FILE}"
        )
        current_path.parent.mkdir(parents=True, exist_ok=True)
        with current_path.open("wb") as file:
            pickle.dump(time_lapse_creator, file)
        if not quiet:
            logger.info(f"State cached in {shorten(str(current_path))}")

    @staticmethod
    def get(logger: logging.Logger, location: str, path_prefix: str) -> object:
        """Retrieves the pickled object in the file. If the file is empty or if it is not found
        it will return an Exception"""
        current_path = Path(
            f"{path_prefix}/{CACHE_DIR}/{CACHE_FILE_PREFIX}{location}{PICKLE_FILE}"
        )
        logger.debug(f"Getting old creator state from {shorten(str(current_path))}")
        if current_path.exists():
            logger.debug("Success!")
            with current_path.open("rb") as file:
                return pickle.load(file)
        else:
            logger.warning("Getting old creator state failed!")
            raise FileNotFoundError()

    @staticmethod
    def clear_cache(
        logger: logging.Logger, location: str, path_prefix: str
    ) -> None:
        """Deletes the cache file for the current TimeLapseCreator given its location"""
        current_path = Path(
            f"{path_prefix}/{CACHE_DIR}/{CACHE_FILE_PREFIX}{location}{PICKLE_FILE}"
        )
        logger.debug(f"Clearing cache file {shorten(str(current_path))}")
        if current_path.exists():
            os.remove(current_path)
            logger.debug("Cache file deleted!")
        else:
            logger.warning("File doesn't exist!")

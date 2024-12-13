import pickle
from pathlib import Path


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

    @classmethod
    def get(cls, location: str, path_prefix: str) -> object:
        """Retrieves the pickled object in the file. If the file is empty or if it is not found
        it will return an Exception"""
        current_path = Path(f"{path_prefix}/cache/cache_{location}.p")
        with current_path.open("rb") as file:
            return pickle.load(file)

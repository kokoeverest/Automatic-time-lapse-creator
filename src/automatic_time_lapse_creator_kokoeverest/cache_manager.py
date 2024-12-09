import pickle


class CacheManager:
    """Class for managing the state of TimeLapseCreator objects. State of the object
    is saved (pickled) in a file and the filename begins with 'cache_' and the location_name of the
    TimeLapseCreator"""

    @classmethod
    def write(cls, time_lapse_creator: object, location: str):
        """Writes the TimeLapseCreator object to a file, overwriting existing objects
        if the file already exists"""
        pickle.dump(time_lapse_creator, open(f"cache_{location}.p", "wb"))

    @classmethod
    def get(cls, location: str):
        """Retrives the pickled object in the file. If the file is empty or if it is not found
        it will return an Exception"""
        return pickle.load(open(f"cache_{location}.p", "rb"))

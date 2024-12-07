import pickle


class CacheManager:
    """"""

    @classmethod
    def write(cls, time_lapse_creator: object, location: str):
        pickle.dump(time_lapse_creator, open(f"cache_{location}.p", "wb"))

    @classmethod
    def get(cls, location: str):
        return pickle.load(open(f"cache_{location}.p", "rb"))

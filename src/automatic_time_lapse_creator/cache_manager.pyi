import logging

logger: logging.Logger

class CacheManager:
    @classmethod
    def write(
        cls, time_lapse_creator: object, location: str, path_prefix: str
    ) -> None: ...
    @classmethod
    def get(cls, location: str, path_prefix: str) -> object: ...

import logging

logger: logging.Logger

class CacheManager:
    @classmethod
    def write(
        cls, time_lapse_creator: object, location: str, path_prefix: str, quiet: bool
    ) -> None: ...
    @classmethod
    def get(cls, location: str, path_prefix: str) -> object: ...
    @classmethod
    def clear_cache(cls, location: str, path_prefix: str) -> None: ...
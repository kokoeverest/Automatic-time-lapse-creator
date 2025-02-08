import logging

# logger: logging.Logger

class CacheManager:
    @classmethod
    def write(
        cls,
        logger: logging.Logger,
        time_lapse_creator: object,
        location: str,
        path_prefix: str,
        quiet: bool = ...,
    ) -> None: ...
    @classmethod
    def get(cls, logger: logging.Logger, location: str, path_prefix: str) -> object: ...
    @classmethod
    def clear_cache(
        cls, logger: logging.Logger, location: str, path_prefix: str
    ) -> None: ...

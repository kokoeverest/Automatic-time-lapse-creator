import logging


class CacheManager:
    @staticmethod
    def write(
        logger: logging.Logger,
        time_lapse_creator: object,
        location: str,
        path_prefix: str,
        quiet: bool = ...,
    ) -> None: ...
    @staticmethod
    def get(logger: logging.Logger, location: str, path_prefix: str) -> object: ...
    @staticmethod
    def clear_cache(
        logger: logging.Logger, location: str, path_prefix: str
    ) -> None: ...

from enum import StrEnum
from logging import Formatter

# File types
JPG_FILE: str
MP4_FILE: str
LOG_FILE: str

# Cacheing configurations
CACHE_DIR: str
CACHE_FILE_PREFIX: str
PICKLE_FILE: str

# Logging configuration
BACKUP_FILES_COUNT: int
LOGS_DIR: str
LOG_INTERVAL: str
LOGGING_FORMAT: str

# Date and time formatting
YYMMDD_FORMAT: str
HHMMSS_UNDERSCORE_FORMAT: str
HHMMSS_COLON_FORMAT: str
MONTH_NAMES: list[str]

# Status codes
OK_STATUS_CODE: int
NO_CONTENT_STATUS_CODE: int

# TimeLapseCreator defaults
DEFAULT_PATH_STRING: str
DEFAULT_CITY_NAME: str
DEFAULT_SECONDS_BETWEEN_FRAMES: int
DEFAULT_NIGHTTIME_RETRY_SECONDS: int
DEFAULT_VIDEO_FPS: int
DEFAULT_VIDEO_WIDTH: int
DEFAULT_VIDEO_HEIGHT: int
DEFAULT_DAY_FOR_MONTHLY_VIDEO: int

# youtube_manager defaults
YOUTUBE_URL_PREFIX: str
DEFAULT_LOG_LEVEL: int
DEFAULT_LOGGING_FORMATTER: Formatter
YOUTUBE_MUSIC_CATEGORY: str
YOUTUBE_KEYWORDS: list[str]
MAX_TITLE_LENGTH: int
BYTES: int
MEGABYTES: int
DEFAULT_CHUNK_SIZE: int

class VideoPrivacyStatus(StrEnum):
    PUBLIC: StrEnum
    PRIVATE: StrEnum
    UNLISTED: StrEnum

# Video defaults
DEFAULT_VIDEO_CODEC: str
DEFAULT_VIDEO_DESCRIPTION: str
MONTHLY_SUMMARY_VIDEO_DESCRIPTION: str
BLACK_BACKGROUND: tuple[int]
WHITE_TEXT: tuple[int]
FILLED_RECTANGLE_VALUE: int

class VideoType(StrEnum):
    DAILY: StrEnum
    MONTHLY: StrEnum

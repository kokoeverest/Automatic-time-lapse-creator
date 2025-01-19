from enum import StrEnum
from logging import DEBUG, Formatter

"""Constants used in the different modules"""

# File types
JPG_FILE: str = ".jpg"
MP4_FILE: str = ".mp4"
LOG_FILE: str = ".log"

# Cacheing configurations
CACHE_DIR: str = ".cache"
CACHE_FILE_PREFIX: str = "cache_"
PICKLE_FILE: str = ".pkl"

# Logging configuration
BACKUP_FILES_COUNT: int = 7
LOGS_DIR: str = ".logs"
LOG_INTERVAL: str = "midnight"
LOGGING_FORMAT: str = "%(name)10s : %(asctime)22s - %(levelname)8s - %(message)s"

# Date and time formatting
YYMMDD_FORMAT: str = "%Y-%m-%d"
HHMMSS_UNDERSCORE_FORMAT: str = "%H_%M_%S"
HHMMSS_COLON_FORMAT: str = "%H:%M:%S %p"

# Status codes
OK_STATUS_CODE: int = 200
NO_CONTENT_STATUS_CODE: int = 204

# TimeLapseCreator default configurations
DEFAULT_PATH_STRING: str = ""
DEFAULT_CITY_NAME: str = "Sofia"
DEFAULT_SECONDS_BETWEEN_FRAMES: int = 60
DEFAULT_NIGHTTIME_RETRY_SECONDS: int = 60
DEFAULT_VIDEO_FPS: int = 30
DEFAULT_VIDEO_WIDTH: int = 640
DEFAULT_VIDEO_HEIGHT: int = 360

# youtube_manager defaults
YOUTUBE_URL_PREFIX = "https://www.youtube.com/watch?v="
DEFAULT_LOG_LEVEL = DEBUG
DEFAULT_LOGGING_FORMATTER = Formatter(LOGGING_FORMAT)
YOUTUBE_MUSIC_CATEGORY = "10"
YOUTUBE_KEYWORDS = ["weather", "ski", "mountain videos"]
MAX_TITLE_LENGTH = 95
MEGABYTES = 1
BYTES = 1024
DEFAULT_CHUNK_SIZE = MEGABYTES * BYTES * BYTES


class VideoPrivacyStatus(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


# Video defaults
DEFAULT_VIDEO_CODEC: str = "mp4v"
DEFAULT_VIDEO_DESCRIPTION = (
    "Video created with Automatic Time Lapse Creator by Kaloyan Peychev"
)
MONTHLY_SUMMARY_VIDEO_DESCRIPTION = "A summary of all daily videos for "


class VideoType(StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"

from enum import Enum
from logging import DEBUG, Formatter
from calendar import month_name

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
LOGGING_FORMAT: str = "[ %(asctime)s ] %(levelname)8s : %(name)14s - %(message)s"
LOG_START: str = "[ 2025-01-25 06:58:30 ]     INFO :"
LOG_START_INT: int = len(LOG_START)

# Date and time formatting
YYMMDD_FORMAT: str = "%Y-%m-%d"
HHMMSS_UNDERSCORE_FORMAT: str = "%H_%M_%S"
HHMMSS_COLON_FORMAT: str = "%H:%M:%S"
MONTH_NAMES = list(month_name)

# Status codes
OK_STATUS_CODE: int = 200
NO_CONTENT_STATUS_CODE: int = 204

# TimeLapseCreator defaults
DEFAULT_PATH_STRING: str = ""
DEFAULT_CITY_NAME: str = "Sofia"
DEFAULT_SECONDS_BETWEEN_FRAMES: int = 60
DEFAULT_NIGHTTIME_RETRY_SECONDS: int = 60
DEFAULT_VIDEO_FPS: int = 30
VIDEO_WIDTH_360p: int = 640
VIDEO_HEIGHT_360p: int = 360
VIDEO_WIDTH_480p: int = int(VIDEO_WIDTH_360p * 1.334)
VIDEO_HEIGHT_480p: int = int(VIDEO_HEIGHT_360p * 1.334)
VIDEO_WIDTH_720p: int = VIDEO_WIDTH_360p * 2
VIDEO_HEIGHT_720p: int = VIDEO_HEIGHT_360p * 2
VIDEO_WIDTH_1080p: int = VIDEO_WIDTH_360p * 3
VIDEO_HEIGHT_1080p: int = VIDEO_HEIGHT_360p * 3
DEFAULT_DAY_FOR_MONTHLY_VIDEO: int = 3

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


class VideoPrivacyStatus(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class AuthMethod(Enum):
    MANUAL = "manual"
    EMAIL = "email"


# Video defaults
DEFAULT_VIDEO_CODEC = "mp4v"
DEFAULT_VIDEO_DESCRIPTION = (
    "Video created with Automatic Time Lapse Creator by Kaloyan Peychev"
)
MONTHLY_SUMMARY_VIDEO_DESCRIPTION = "A summary of all daily videos for "
BLACK_BACKGROUND = (0, 0, 0)
WHITE_TEXT = (255, 255, 255)
FILLED_RECTANGLE_VALUE = -1

class VideoType(Enum):
    DAILY = "daily"
    MONTHLY = "monthly"

# LocationAndTimeManager defaults
DEFAULT_SUNSET_OFFSET = 50
DEFAULT_SUNRISE_OFFSET = 50

# WeatherStationInfo defaults
OLD_TIMESTAMP_HOURS = 5
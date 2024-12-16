"""Constants used in the different modules"""

# File types
JPG_FILE: str = ".jpg"
MP4_FILE: str = ".mp4"
LOG_FILE: str = ".log"

# Logging configuration
LOGS_DIR: str = "/logs"
LOG_INTERVAL: str = "midnight"
LOGGING_FORMAT: str = "%(name)s: %(asctime)s - %(levelname)s - %(message)s"

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
DEFAULT_NIGHTTIME_RETRY_SECONDS: int = 300
DEFAULT_VIDEO_FPS: int = 30
DEFAULT_VIDEO_WIDTH: int = 640
DEFAULT_VIDEO_HEIGHT: int = 360

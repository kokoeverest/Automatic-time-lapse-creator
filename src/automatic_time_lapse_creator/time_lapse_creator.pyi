from __future__ import annotations
from .cache_manager import CacheManager as CacheManager
from queue import Queue
from .common.constants import (
    DEFAULT_CITY_NAME as DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS as DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_PATH_STRING as DEFAULT_PATH_STRING,
    DEFAULT_SECONDS_BETWEEN_FRAMES as DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS as DEFAULT_VIDEO_FPS,
    VIDEO_HEIGHT_360p as VIDEO_HEIGHT_360p,
    VIDEO_WIDTH_360p as VIDEO_WIDTH_360p,
    HHMMSS_COLON_FORMAT as HHMMSS_COLON_FORMAT,
    HHMMSS_UNDERSCORE_FORMAT as HHMMSS_UNDERSCORE_FORMAT,
    JPG_FILE as JPG_FILE,
    LOGGING_FORMAT as LOGGING_FORMAT,
    LOGS_DIR as LOGS_DIR,
    LOG_FILE as LOG_FILE,
    LOG_INTERVAL as LOG_INTERVAL,
    MP4_FILE as MP4_FILE,
    OK_STATUS_CODE as OK_STATUS_CODE,
    YYMMDD_FORMAT as YYMMDD_FORMAT,
)
from .common.exceptions import (
    InvalidCollectionException as InvalidCollectionException,
    InvalidStatusCodeException as InvalidStatusCodeException,
)
from .common.utils import create_log_message as create_log_message
from .source import Source as Source
from .time_manager import LocationAndTimeManager as LocationAndTimeManager
from . import text_box as box
from logging import Logger
from typing import Any, Iterable

class TimeLapseCreator:
    base_path: str
    folder_name: str
    location: LocationAndTimeManager
    sources: set[Source]
    wait_before_next_frame: int
    nighttime_wait_before_next_retry: int
    video_fps: int
    video_width: int
    video_height: int
    text_box_position: type[box.TextBox] | None = ...
    text_box_transparency: float = ...
    quiet_mode: bool
    video_queue: Queue[Any | None] | None = ...
    log_queue: Queue[Any] | None = ...
    logger: Logger
    def __init__(
        self,
        sources: Iterable[Source] = ...,
        city: str = ...,
        path: str = ...,
        seconds_between_frames: int = ...,
        night_time_retry_seconds: int = ...,
        video_fps: int = ...,
        video_width: int = ...,
        video_height: int = ...,
        text_box_position: type[box.TextBox] | None = box.TopInsideTextBox,
        text_box_transparency: float = box.TextBox.TRANSPARENCY_MID,
        quiet_mode: bool = True,
        log_queue: Queue[Any] | None = ...,
        create_monthly_summary_video: bool = ...,
        day_for_monthly_summary_video: int = ...,
        delete_daily_videos_after_monthly_summary_is_created: bool = ...,
        sunrise_offset_minutes: int = ...,
        sunset_offset_minutes: int = ...,
    ) -> None: ...
    def get_cached_self(self) -> TimeLapseCreator: ...
    def cache_self(self) -> None: ...
    def clear_cache(self) -> None: ...
    def execute(
        self,
        video_queue: Queue[Any] | None = ...,
        log_queue: Queue[Any] | None = ...,
    ) -> None: ...
    def collect_images_from_webcams(self) -> bool: ...
    def is_it_next_day(self) -> None: ...
    def create_video(
        self, source: Source, delete_source_images: bool = True
    ) -> bool: ...
    def verify_sources_not_empty(self) -> None: ...
    def reset_images_partially_collected(self) -> None: ...
    def reset_all_sources_counters_to_default_values(self) -> None: ...
    def set_sources_all_images_collected(self) -> None: ...
    def add_sources(self, sources: Source | Iterable[Source]) -> None: ...
    def source_exists(self, source: Source) -> bool: ...
    def remove_sources(self, sources: Source | Iterable[Source]) -> None: ...
    @classmethod
    def check_sources(
        cls, sources: Source | Iterable[Source]
    ) -> Source | set[Source]: ...
    @classmethod
    def validate_collection(cls, sources: Iterable[Source]) -> set[Source]: ...
    def reset_test_counter(self) -> None: ...
    @staticmethod
    def valid_folder(*args: str) -> bool: ...
    def get_video_files_paths(
        self, base_folder: str, year: str, month: str
    ) -> list[str]: ...
    def create_monthly_video(
        self,
        base_path: str,
        year: str,
        month: str,
        delete_source_files: bool = ...,
        extension: str = ...,
    ) -> str | None: ...
    def is_next_month(self) -> bool: ...
    def process_monthly_summary(self) -> None: ...
    def get_previous_year_and_month(self) -> str: ...

#     class TimeLapseCreator(ABC):
#     base_path: str
#     folder_name: str
#     sources: set[Source]
#     wait_before_next_frame: int
#     video_fps: int
#     video_width: int
#     video_height: int
#     quiet_mode: bool
#     video_queue: Queue[Any | None] | None = ...
#     log_queue: Queue[Any] | None = ...
#     logger: Logger
#     def __init__(
#         self,
#         sources: Iterable[Source] = ...,
#         city: str = ...,
#         path: str = ...,
#         seconds_between_frames: int = ...,
#         video_fps: int = ...,
#         video_width: int = ...,
#         video_height: int = ...,
#         quiet_mode: bool = True,
#         log_queue: Queue[Any] | None = ...,
#         create_monthly_summary_video: bool = ...,
#         day_for_monthly_summary_video: int = ...,
#         delete_daily_videos_after_monthly_summary_is_created: bool = ...,
#     ) -> None: ...
#     def get_cached_self(self) -> TimeLapseCreator: ...
#     def cache_self(self) -> None: ...
#     def clear_cache(self) -> None: ...
#     @abstractmethod
#     def execute(
#         self,
#         video_queue: Queue[Any] | None = ...,
#         log_queue: Queue[Any] | None = ...,
#     ) -> None: ...
#     @abstractmethod
#     def collect_images(self) -> bool: ...
#     @abstractmethod
#     def create_video(
#         self, source: Source, delete_source_images: bool = True
#     ) -> bool: ...
#     def verify_sources_not_empty(self) -> None: ...
#     def reset_images_partially_collected(self) -> None: ...
#     def reset_all_sources_counters_to_default_values(self) -> None: ...
#     def set_sources_all_images_collected(self) -> None: ...
#     def add_sources(self, sources: Source | Iterable[Source]) -> None: ...
#     def source_exists(self, source: Source) -> bool: ...
#     def remove_sources(self, sources: Source | Iterable[Source]) -> None: ...
#     @classmethod
#     def check_sources(
#         cls, sources: Source | Iterable[Source]
#     ) -> Source | set[Source]: ...
#     @classmethod
#     def validate_collection(cls, sources: Iterable[Source]) -> set[Source]: ...
#     def reset_test_counter(self) -> None: ...
#     @staticmethod
#     def valid_folder(*args: str) -> bool: ...
#     def get_video_files_paths(
#         self, base_folder: str, year: str, month: str
#     ) -> list[str]: ...
#     def create_monthly_video(
#         self,
#         base_path: str,
#         year: str,
#         month: str,
#         delete_source_files: bool = ...,
#         extension: str = ...,
#     ) -> str | None: ...
#     def is_next_month(self) -> bool: ...
#     def process_monthly_summary(self) -> None: ...
#     def get_previous_year_and_month(self) -> str: ...


# class WebCamTimeLapseCreator(TimeLapseCreator):
#     location: LocationAndTimeManager
#     nighttime_wait_before_next_retry: int
#     def __init__(
#         self,
#         city: str = ...,
#         night_time_retry_seconds: int = ...,
#         sunrise_offset_minutes: int = ...,
#         sunset_offset_minutes: int = ...,
#     ) -> None: ...
#     def is_it_next_day(self) -> None: ...
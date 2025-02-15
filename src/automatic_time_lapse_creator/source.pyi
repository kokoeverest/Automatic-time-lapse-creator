from logging import Logger
from typing import Any
from queue import Queue
from .weather_station_info import WeatherStationInfo

class Source:
    logger: Logger
    location_name: str
    url: str
    url_is_video_stream: bool
    weather_data_provider: WeatherStationInfo | None
    def __init__(
        self,
        location_name: str,
        url: str,
        log_queue: Queue[Any] | None = ...,
        is_video_stream: bool = ...,
        weather_data_on_images: bool = ...,
        weather_data_provider: WeatherStationInfo | None = ...,
    ) -> None: ...
    @property
    def has_weather_data(self) -> bool: ...
    @property
    def is_valid_stream(self) -> bool: ...
    @property
    def is_valid_url(self) -> bool: ...
    @property
    def images_collected(self) -> bool: ...
    @property
    def images_partially_collected(self) -> bool: ...
    @property
    def images_count(self) -> int: ...
    @property
    def daily_video_created(self) -> bool: ...
    @property
    def monthly_video_created(self) -> bool: ...
    def set_daily_video_created(self) -> None: ...
    def reset_daily_video_created(self) -> None: ...
    def set_monthly_video_created(self) -> None: ...
    def reset_monthly_video_created(self) -> None: ...
    def increase_images(self) -> None: ...
    def reset_images_counter(self) -> None: ...
    def set_all_images_collected(self) -> None: ...
    def set_images_partially_collected(self) -> None: ...
    def reset_all_images_collected(self) -> None: ...
    def reset_images_partially_collected(self) -> None: ...
    def get_frame_bytes(self) -> bytes | None: ...
    @classmethod
    def validate_stream_url(cls, url: str, logger: Logger) -> bool: ...
    @classmethod
    def validate_url(cls, url: str, logger: Logger) -> bool: ...
    @classmethod
    def get_url_with_yt_dlp(cls, url: str) -> str: ...
    def fetch_image_from_stream(self) -> bytes | None: ...
    def fetch_image_from_static_web_cam(self) -> bytes | Any: ...
from pathlib import Path
from logging import Logger

from .text_box import TextBox


class VideoManager:
    @staticmethod
    def video_exists(path: str | Path) -> bool: ...
    @staticmethod
    def create_timelapse(
        logger: Logger,
        path: str,
        output_video: str,
        fps: int,
    ) -> bool: ...
    @staticmethod
    def delete_source_media_files(
        logger: Logger,
        path: str | Path,
        extension: str = ...,
        delete_folder: bool = ...,
    ) -> bool: ...
    @classmethod
    def create_monthly_summary_video(
        cls,
        logger: Logger,
        video_paths: list[str],
        output_video_path: str,
        fps: int,
    ) -> bool: ...
    @staticmethod
    def save_image_with_weather_overlay(
        image_bytes: bytes,
        save_path: str,
        width: int,
        height: int,
        date_time_text: str = ...,
        weather_data_text: str | None = ...,
        text_box_position: type[TextBox] | None = ...,
        text_box_transparency: float = ...,
    ) -> bool: ...
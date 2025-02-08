from pathlib import Path
from logging import Logger


class VideoManager:
    @classmethod
    def video_exists(cls, path: str | Path) -> bool: ...
    @classmethod
    def create_timelapse(
        cls,
        logger: Logger,
        path: str,
        output_video: str,
        fps: int,
    ) -> bool: ...
    @classmethod
    def delete_source_media_files(
        cls,
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
    @classmethod
    def save_image_with_weather_overlay(
        cls,
        image_bytes: bytes,
        save_path: str,
        width: int,
        height: int,
        date_time_text: str = ...,
        weather_data_text: str | None = ...,
    ) -> bool: ...
from pathlib import Path
from logging import Logger

# logger: Logger

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
        width: int,
        height: int,
        with_stamp: bool = ...,
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
        width: int,
        height: int,
    ) -> bool: ...

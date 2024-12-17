from pathlib import Path
from logging import Logger

logger = Logger

class VideoManager:
    @classmethod
    def video_exists(cls, path: str | Path) -> bool: ...
    @classmethod
    def create_timelapse(
        cls,
        path: str,
        output_video: str,
        fps: int,
        width: int,
        height: int,
        with_stamp: bool = True,
    ) -> bool: ...
    @classmethod
    def delete_source_images(cls, path: str | Path) -> bool: ...

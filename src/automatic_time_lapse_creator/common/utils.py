import os
import json
from abc import ABC
from .constants import (
    DEFAULT_VIDEO_DESCRIPTION,
    MONTHLY_SUMMARY_VIDEO_DESCRIPTION,
    MONTH_NAMES,
)


class VideoResponse(ABC):
    video_type: str
    source_location_name: str | None
    wait_before_next_frame: int | None
    nighttime_wait_before_next_retry: int | None
    video_fps: int | None
    video_width: int | None
    video_height: int | None
    delete_collected_daily_images: bool | None
    delete_daily_videos_after_monthly_summary_is_created: bool | None
    location_city_name: str | None
    location_city_tz: str | None
    location_sunrise_offset_minutes: int | None
    location_sunset_offset_minutes: int | None

    def __init__(self, video_path: str, video_created: bool) -> None:
        self.video_path = video_path
        self.video_created = video_created

    def to_json(self):
        return json.dumps(self.__dict__)

class DailyVideoResponse(VideoResponse):
    def __init__(
            self, 
            video_path: str, 
            video_type: str, 
            images_count: int, 
            video_created: bool, 
            all_images_collected: bool,
            images_partially_collected: bool
    ) -> None:
        super().__init__(video_path = video_path, video_created=video_created)
        self.video_type = video_type
        self.images_count = images_count
        self.all_images_collected = all_images_collected
        self.images_partially_collected = images_partially_collected

class MonthlyVideoResponse(VideoResponse):
    def __init__(
            self, 
            video_path: str, 
            video_created: bool, 
            video_type: str, 
            video_files_count: int
    ) -> None:
        super().__init__(video_path, video_created)
        self.video_type = video_type
        self.video_files_count= video_files_count


def create_log_message(location: str, url: str, method: str) -> str:
    """
    Creates an appropriate log message according to the method which calls it

    Returns::

        str - the log message if the method is 'add' or 'remove'"""
    if method == "add":
        return f"Source with location: {location} or url: {url} already exists!"
    elif method == "remove":
        return f"Source with location: {location} or url: {url} doesn't exist!"
    else:
        return f"Unknown command: {method}"


def shorten(path: str) -> str:
    """
    Receives a file path and trims the first part returning a more readable,
    short version of it

    Returns::

        str - the shortened path
    """
    sep = os.path.sep
    start_idx = 2 if os.path.isdir(path) else 3

    head, tail = os.path.split(path)
    head = sep.join(head.split(sep)[-start_idx:])
    return f"{head}{sep}{tail}"


def dash_sep_strings(*args: str):
    """Create a dash separated string from many strings in the format:
    "str1-str2-str3" etc.
    """
    return "-".join(args)


def create_description_for_monthly_video(monthly_video: str):
    """Creates a comprehensive description for the monthly summary videos.

    Args::
        monthly_video: str - the video path of the monthly video

    Returns::
        str - the created description
    """
    _, tail = os.path.split(monthly_video)
    year = tail[:4]
    month = tail[5:7]
    month_name = MONTH_NAMES[int(month)]
    suffix = f"{month_name}, {year}"

    result = f"{MONTHLY_SUMMARY_VIDEO_DESCRIPTION}{suffix}\n{DEFAULT_VIDEO_DESCRIPTION}"
    return result

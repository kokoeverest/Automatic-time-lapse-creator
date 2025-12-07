from abc import ABC

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
    video_path: str
    video_created: bool
    def __init__(self, video_path: str, video_created: bool) -> None: ...
    def to_json(self) -> str: ...
        

class DailyVideoResponse(VideoResponse):
    images_count: int
    all_images_collected: bool
    images_partially_collected: bool
    def __init__(
            self, 
            video_path: str, 
            video_type: str, 
            images_count: int, 
            video_created: bool, 
            all_images_collected: bool,
            images_partially_collected: bool
    ) -> None: ...

class MonthlyVideoResponse(VideoResponse):
    video_files_count: int
    def __init__(
            self, 
            video_path: str, 
            video_created: bool, 
            video_type: str, 
            video_files_count: int
    ) -> None: ...

def create_log_message(location: str, url: str, method: str) -> str: ...

def shorten(path: str) -> str: ...

def dash_sep_strings(*args: str) -> str: ...

def create_description_for_monthly_video(monthly_video: str) -> str: ...
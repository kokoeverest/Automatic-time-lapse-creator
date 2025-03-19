from src.automatic_time_lapse_creator.common.constants import (
    NO_CONTENT_STATUS_CODE,
    JPG_FILE,
    MP4_FILE,
    DEFAULT_VIDEO_FPS,
    VIDEO_HEIGHT_360p,
    VIDEO_WIDTH_360p,
    DEFAULT_DAY_FOR_MONTHLY_VIDEO
)
from src.automatic_time_lapse_creator.youtube_manager import YouTubeAuth
from src.automatic_time_lapse_creator.source import Source
from src.automatic_time_lapse_creator.weather_station_info import MeteoRocks
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
from cv2.typing import MatLike
from cv2 import VideoCapture
from astral import LocationInfo
from astral.geocoder import GroupInfo
import os
import numpy as np


today = datetime.today()


def mock_None():
    return


mock_group_info = Mock(spec=GroupInfo)
mock_location_info = Mock(spec=LocationInfo)
mock_save_file_path = "test_output.jpg"

def mock_jpg_file(number: int = 1):
    mock_file = Mock()
    mock_file.name = f"test_image_{number}{JPG_FILE}"
    mock_file.read.return_value = b"fake image data"
    return mock_file.name


def mock_mat_like():
    mat_like = MagicMock(spec=MatLike)
    mat_like.shape = [600, 300, 10]

    return mat_like

def mock_images_iterator():
    return (mock_jpg_file(x) for x in range(1, 11))

mock_image = mock_jpg_file()
mock_MatLike = mock_mat_like()
mock_path_to_images_folder = os.path.join("fake", "folder", "path")
mock_output_video_name = f"fake_video{MP4_FILE}"
mock_video_frames_per_second = DEFAULT_VIDEO_FPS
mock_video_width = VIDEO_WIDTH_360p
mock_video_height = VIDEO_HEIGHT_360p

mock_Size = ((185, 12), 1)


class MockResponse:
    status_code = NO_CONTENT_STATUS_CODE


class MockDatetime:
    fake_daylight = datetime(
        today.year, today.month, today.day, 12, 00, 00, tzinfo=timezone.utc
    )
    fake_nighttime = datetime(
        today.year, today.month, today.day, 23, 59, 00, tzinfo=timezone.utc
    )
    fake_today = datetime(year=2024, month=1, day=1)
    fake_next_day = datetime(fake_today.year, fake_today.month, fake_today.day + 1)
    fake_next_month = datetime(fake_today.year, fake_today.month + 1, fake_today.day)
    fake_next_year = datetime(fake_today.year + 1, fake_today.month, fake_today.day)
    fake_day_for_a_monthly_video = datetime(year=2024, month=1, day=DEFAULT_DAY_FOR_MONTHLY_VIDEO)
    fake_now = datetime(year=2024, month=2, day=DEFAULT_DAY_FOR_MONTHLY_VIDEO, hour=3)
    fake_now_wrong_hour = fake_day_for_a_monthly_video

mock_youTubeAuth = Mock(spec=YouTubeAuth)

mock_weather_info_provider = Mock(spec=MeteoRocks)

def mock_source_with_weather_info_provider():
    mock_src = Mock(spec=Source)
    mock_src.weather_data_provider = mock_weather_info_provider

    return mock_src

def mock_source_valid_video_stream():
    mock_src = MagicMock(spec=Source)
    mock_src.url_is_video_stream = True
    mock_src.is_valid_stream = True

    return mock_src

mock_capture = MagicMock(spec=VideoCapture)

mock_bytes = np.zeros((100, 100, 3), dtype=np.uint8).tobytes()
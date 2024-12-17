from src.automatic_time_lapse_creator.common.constants import (
    NO_CONTENT_STATUS_CODE,
    JPG_FILE,
    MP4_FILE,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_VIDEO_WIDTH,
)
from datetime import datetime, timezone
from unittest.mock import Mock
from cv2.typing import MatLike
from astral import LocationInfo
from astral.geocoder import GroupInfo

today = datetime.today()

def mock_None():
    return

mock_group_info = Mock(spec=GroupInfo)
mock_location_info = Mock(spec=LocationInfo)

def mock_jpg_file(number: int = 1):
    mock_file = Mock()
    mock_file.name = f"test_image_{number}{JPG_FILE}"
    mock_file.read.return_value = b"fake image data"
    return mock_file.name


def mock_mat_like():
    mat_like = Mock(spec=MatLike)

    return mat_like


mock_image = mock_jpg_file()
mock_images_list = [mock_jpg_file(x) for x in range(1, 11)]
mock_MatLike = mock_mat_like()
mock_path_to_images_folder = "fake/folder/path"
mock_output_video_name = f"fake_video{MP4_FILE}"
mock_video_frames_per_second = DEFAULT_VIDEO_FPS
mock_video_width = DEFAULT_VIDEO_WIDTH
mock_video_height = DEFAULT_VIDEO_HEIGHT

mock_Size = ((185, 12), 1)


class MockResponse:
    status_code = NO_CONTENT_STATUS_CODE


class MockDatetime:
    fake_daylight = datetime(today.year, today.month, today.day, 12, 00, 00, tzinfo=timezone.utc)
    fake_nighttime = datetime(
        today.year, today.month, today.day, 23, 59, 00, tzinfo=timezone.utc
    )
    fake_today = datetime(year=2024, month=1, day=1)
    fake_next_day = datetime(fake_today.year, fake_today.month, fake_today.day + 1)
    fake_next_month = datetime(fake_today.year, fake_today.month + 1, fake_today.day)
    fake_next_year = datetime(fake_today.year + 1, fake_today.month, fake_today.day)

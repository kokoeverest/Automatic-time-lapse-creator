from src.automatic_time_lapse_creator_kokoeverest.common.constants import *
from datetime import datetime
from unittest.mock import Mock
from cv2.typing import MatLike

today = datetime.today()

def mock_jpg_file(number: int=1):
    mock_file = Mock()
    mock_file.name = f"test_image_{number}.jpg"
    mock_file.read.return_value = b"fake image data"
    return mock_file.name


def mock_mat_like():
    mat_like = Mock(spec=MatLike)

    return mat_like

mock_image = mock_jpg_file()
mock_images_list = [mock_jpg_file(x) for x in range(1, 11)]
mock_MatLike = mock_mat_like()
mock_path_to_images_folder = "fake/folder/path"
mock_output_video_name = "fake_video.mp4"
mock_video_frames_per_second = 30
mock_video_width = 640
mock_video_height = 360


class MockResponse:
    status_code = NO_CONTENT_STATUS_CODE


class MockIsDaylight:
    @classmethod
    def false_return(cls):
        return False

    @classmethod
    def true_return(cls):
        return True


class MockDatetime:
    fake_daylight = datetime(today.year, today.month, today.day, 12, 00, 00)
    fake_nighttime = datetime(today.year, today.month, today.day, 00, 00, 00)


class MockTimeAndLocationManager:
    start_of_daylight = datetime(today.year, today.month, today.day, 7, 00, 00)
    end_of_daylight = datetime(today.year, today.month, today.day, 18, 00, 00)

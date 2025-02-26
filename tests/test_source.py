from queue import Queue
import pytest
import tests.test_data as td
import tests.test_mocks as tm
from src.automatic_time_lapse_creator.source import ImageSource, StreamSource, Source
from src.automatic_time_lapse_creator.common.constants import (
    YOUTUBE_URL_PREFIX,
    OK_STATUS_CODE,
)
from unittest.mock import MagicMock, Mock, patch
from requests import Response
from logging import Logger


@pytest.fixture
def sample_source():
    return td.sample_source_no_weather_data


@pytest.fixture
def source_with_weather_provider():
    return tm.mock_source_with_weather_info_provider()


@pytest.fixture
def source_valid_video_stream():
    return tm.mock_source_valid_video_stream()


@pytest.fixture
def sample_StreamSource():
    return StreamSource(location_name="fake", url="fake_stream_url")


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=Logger)
    yield mock_logger
    mock_logger.reset_mock()


mock_log_queue = Mock(spec=Queue)


def test_source_initializes_correctly_with_default_config(mock_logger: Mock):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch(
            "src.automatic_time_lapse_creator.source.ImageSource.validate_url",
            return_value=True,
        ) as mock_validate,
    ):
        sample_source = ImageSource(
            td.valid_source_name, td.valid_url
        )
        assert isinstance(sample_source, Source)
        assert sample_source.location_name == td.valid_source_name
        assert sample_source.url == td.valid_url
        assert not sample_source.daily_video_created
        assert not sample_source.monthly_video_created
        assert sample_source.images_count == 0
        assert not sample_source.images_collected
        assert not sample_source.images_partially_collected
        assert sample_source.is_valid_url
        assert not sample_source.has_weather_data
        assert not sample_source.weather_data_provider
        assert mock_logger.call_count == 0

        mock_validate.assert_called_with(sample_source.url)


def test_source_initializes_correctly_with_weather_data_provider(mock_logger: Logger):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.ImageSource.validate_url",
            return_value=True,
        ),
    ):
        actual_result = ImageSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
            weather_data_provider=tm.mock_source_with_weather_info_provider(),
        )

    # Assert
    assert actual_result.is_valid_url
    assert not actual_result.has_weather_data
    assert actual_result.weather_data_provider
    assert mock_logger.call_count == 1


def test_source_initializes_correctly_for_video_stream(mock_logger: Logger):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=True,
        ),
    ):
        actual_result = StreamSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
        )

    # Assert
    assert actual_result.is_valid_url
    assert not actual_result.has_weather_data
    assert not actual_result.weather_data_provider
    assert mock_logger.call_count == 0


def test_source_sets_is_valid_stream_to_False_for_invalid_video_stream(
    mock_logger: Logger,
):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=False,
        ),
    ):
        actual_result = StreamSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
        )

    # Assert
    assert not actual_result.is_valid_url
    assert not actual_result.has_weather_data
    assert not actual_result.weather_data_provider
    assert mock_logger.call_count == 0


def test_set_video_created_changes_video_created_to_True(sample_source: Source):
    # Arrange & Act
    sample_source.set_daily_video_created()

    # Assert
    assert sample_source.daily_video_created


def test_reset_video_created_changes_video_created_to_False(sample_source: Source):
    # Arrange & Act
    sample_source.reset_daily_video_created()

    # Assert
    assert not sample_source.daily_video_created


def test_set_monthly_video_created_changes_monthly_video_created_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_monthly_video_created()

    # Assert
    assert sample_source.monthly_video_created


def test_reset_monthly_video_created_changes_monthly_video_created_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_monthly_video_created()

    # Assert
    assert not sample_source.monthly_video_created


def test_increase_images_increases_the_images_count_by_one(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()

    # Assert
    assert sample_source.images_count == 1


def test_reset_images_counter_resets_the_images_count_to_zero(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()
    sample_source.reset_images_counter()

    # Assert
    assert sample_source.images_count == 0


def test_set_all_images_collected_sets_all_images_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_all_images_collected()

    # Assert
    assert sample_source.images_collected


def test_reset_all_images_collected_resets_all_images_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_all_images_collected()

    # Assert
    assert not sample_source.images_collected


def test_set_images_partially_collected_sets_images_partially_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_images_partially_collected()

    # Assert
    assert sample_source.images_partially_collected


def test_reset_images_partially_collected_resets_images_partially_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_images_partially_collected()

    # Assert
    assert not sample_source.images_partially_collected


def test_validate_stream_url_returns_True_if_url_is_valid_stream(
    sample_StreamSource: StreamSource, mock_logger: Mock
):
    # Arrange
    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.get_url_with_yt_dlp",
            return_value="",
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = (True, tm.mock_MatLike)
        mock_cap_instance.release.return_value = None

        # Act
        actual_result = sample_StreamSource.validate_url(
            sample_StreamSource.url
        )

        # Assert
        mock_cap_instance.read.assert_called()
        mock_cap_instance.release.assert_called()
        mock_logger.warning.assert_not_called()
        assert actual_result


def test_validate_stream_url_returns_False_if_url_is_invalid_stream(
    sample_StreamSource: StreamSource,
    mock_logger: Mock,
):
    # Arrange
    invalid_url_return = "mock_invalid_url"
    sample_StreamSource.logger = mock_logger
    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch.object(
            StreamSource,
            "get_url_with_yt_dlp",
            return_value=invalid_url_return,
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = (False, None)

        # Act
        actual_result = sample_StreamSource.validate_url(
            YOUTUBE_URL_PREFIX
        )

        # Assert
        assert not actual_result
        sample_StreamSource.logger.warning.assert_called_once_with(
            f"{sample_StreamSource.location_name}: {invalid_url_return} is not a valid url and will be ignored!"
        )


def test_validate_stream_url_returns_False_if_Exception_occured(
    sample_StreamSource: StreamSource, mock_logger: Mock
):
    sample_StreamSource.logger = mock_logger
    # Arrange
    invalid_url_return = "mock_invalid_url"

    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch.object(
            StreamSource,
            "get_url_with_yt_dlp",
            return_value=invalid_url_return,
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = Exception

        # Act
        actual_result = sample_StreamSource.validate_url(
            YOUTUBE_URL_PREFIX
        )

        # Assert
        assert not actual_result
        mock_logger.error.assert_called_once()


def test_validate_url_returns_False_if_Exception_occured(
    sample_source: ImageSource, mock_logger: Mock
):
    # Arrange
    sample_source.logger = mock_logger
    with patch("requests.get", side_effect=Exception):
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert not actual_result
        mock_logger.error.assert_called_once()


def test_validate_url_returns_False_if_returned_content_is_not_bytes(
    sample_source: ImageSource,
    mock_logger: Mock,
):
    # Arrange
    sample_source.logger = mock_logger
    with (
        patch("requests.get", return_value=Mock(spec=Response)) as mock_response,
    ):
        mock_response.content = "<html>"
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert not actual_result
        mock_logger.warning.assert_called_once()


def test_validate_url_returns_True_if_returned_content_is_bytes(
    sample_source: ImageSource, mock_logger: Mock
):
    # Arrange
    sample_source.logger = mock_logger
    mock_response = Mock(spec=Response)
    mock_response.status_code = OK_STATUS_CODE
    mock_response.content = b"some_content"
    with patch("requests.get", return_value=mock_response):
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert actual_result
        mock_logger.info.assert_called_once()


def test_get_frame_bytes_returns_correct_result_for_ImageSource(
    sample_source: ImageSource,
):
    # Arrange
    expected_result = b"some content"
    with patch.object(
        sample_source, "get_frame_bytes", return_value=expected_result
    ) as mock_source:
        # Act
        actual_result = sample_source.get_frame_bytes()

    # Assert
    assert actual_result == expected_result
    mock_source.assert_called_once()
    assert mock_source.fetch_image_from_stream.call_count == 0


def test_get_frame_bytes_returns_correct_result_for_StreamSource(
    sample_StreamSource: StreamSource
):
    # Arrange
    expected_result = b"some content"
    with (
        patch.object(
            sample_StreamSource,
            "get_frame_bytes",
            return_value=expected_result,
        ) as mock_source,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=True,
        ),
    ):
        # Act
        actual_result = sample_StreamSource.get_frame_bytes()

    # Assert
    mock_source.assert_called_once()
    assert mock_source.fetch_image_from_static_web_cam.call_count == 0
    assert actual_result == expected_result

from unittest.mock import patch, MagicMock
import pytest
from logging import Logger

from src.automatic_time_lapse_creator.youtube_manager import YouTubeAuth, YouTubeChannelManager
from src.automatic_time_lapse_creator.common.constants import VideoPrivacyStatus
import tests.test_data as td


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=Logger)
    yield mock_logger
    mock_logger.reset_mock()

@pytest.fixture
def mock_youtube_auth():
    auth = MagicMock(spec=YouTubeAuth)
    auth.service = MagicMock()
    return auth

@pytest.fixture
def mock_channel_man(
    mock_logger: Logger,
    mock_youtube_auth: YouTubeAuth
    ):
    channel_man = YouTubeChannelManager(logger=mock_logger, youtube_client=mock_youtube_auth)
    return channel_man


def test_youtube_channelman_initializes_correctly(mock_logger: Logger, mock_youtube_auth: YouTubeAuth):
    # Arrange
    with patch("src.automatic_time_lapse_creator.youtube_manager.configure_child_logger", return_value= mock_logger):

        # Act
        result = YouTubeChannelManager(mock_youtube_auth, mock_logger)

    # Assert
    assert isinstance(result, YouTubeChannelManager)
    assert result.youtube is mock_youtube_auth
    assert result.logger is mock_logger


def test_filter_pending_videos_returns_correct_list():
    # Arrange
    mock_videos_list = [
        {"uploadStatus": "uploaded"},
        {"uploadStatus": "pending"},
        {"uploadStatus": "pending"},
        {"uploadStatus": "uploaded"},
    ]

    # Act
    result = YouTubeChannelManager.filter_pending_videos(mock_videos_list)

    # Assert

    assert len(result) == 2

    # Arrange
    # Act
    # Assert

def test_list_channel_returns_videos_successfully(mock_channel_man: YouTubeChannelManager):
    # Arrange
    mock_return_list: list[dict[str, str]] = [{
                "id": td.sample_video_id,
                "title": td.sample_video_title,
                "uploadStatus": "uploaded",
                "privacyStatus": VideoPrivacyStatus.PUBLIC.value,
            }]
    with (
        patch.object(mock_channel_man.youtube.service.search().list(),
            "execute",
            return_value=td.mock_video_response),
        patch.object(mock_channel_man, "get_video_details", return_value=mock_return_list)
        ):
    # Act
        result = mock_channel_man.list_channel()
    # Assert
    mock_channel_man.logger.info.assert_called_once_with("Fetching channel details")
    assert result and result == mock_return_list
    assert len(result) == 1

def test_list_channel_returns_None_if_Exception_occurs(mock_channel_man: YouTubeChannelManager):
    # Arrange
    with (
        patch.object(
            mock_channel_man.youtube.service.search().list(),
            "execute",
            side_effect=Exception("API Error"),
        ),
        patch.object(mock_channel_man, "get_video_details"),
    ):
        # Act
        result = mock_channel_man.list_channel()

    # Assert
    mock_channel_man.logger.error.assert_called_once()
    assert result is None 

def test_get_video_details_returns_list_with_video_details(mock_channel_man: YouTubeChannelManager):
    # Arrange
    mock_videos_list: list[str] = [td.sample_video_id]
    with patch.object(mock_channel_man.youtube.service.videos().list(),
            "execute",
            return_value=td.mock_video_list_response):
        
    # Act
        result = mock_channel_man.get_video_details(mock_videos_list)
    # Assert

    assert next(result) is not None

def test_delete_video_returns_True_when_successful(mock_channel_man: YouTubeChannelManager):
    # Arrange    
    with patch.object(
        mock_channel_man.youtube.service.videos().delete(),
        "execute",
        return_value=None,
    ) as mock_execute:
        # Act
        result = mock_channel_man.delete_video("abc123")

    # Assert
    assert result
    mock_execute.assert_called_once()
    mock_channel_man.logger.info.assert_called_once_with("Success")


def test_delete_video_returns_False_on_Exception(mock_channel_man: YouTubeChannelManager):
    # Arrange
    with patch.object(
        mock_channel_man.youtube.service.videos().delete(),
        "execute",
        side_effect=Exception("API error"),
    ) as mock_execute:
        # Act
        result = mock_channel_man.delete_video("abc123")

    # Assert
    assert not result
    mock_execute.assert_called_once()
    mock_channel_man.logger.error.assert_called_once_with("Failed: ", exc_info=True)
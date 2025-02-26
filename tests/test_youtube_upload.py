from unittest.mock import patch, MagicMock
import pytest
import os
from logging import Logger

from src.automatic_time_lapse_creator.youtube_manager import YouTubeAuth, YouTubeUpload
from src.automatic_time_lapse_creator.common.constants import (
    DEFAULT_VIDEO_DESCRIPTION,
    MP4_FILE,
    YOUTUBE_MUSIC_CATEGORY,
    YOUTUBE_KEYWORDS,
    YOUTUBE_URL_PREFIX,
    DEFAULT_CHUNK_SIZE,
    VideoPrivacyStatus,
)
import tests.test_data as td
from httplib2.error import HttpLib2Error


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=Logger)
    yield mock_logger
    mock_logger.reset_mock()


def mock_youtube_auth():
    auth = MagicMock(spec=YouTubeAuth)
    auth.service = MagicMock()
    return auth


@pytest.fixture
def mock_uploader(mock_logger: MagicMock):
    uploader = YouTubeUpload(
        logger=mock_logger,
        source_directory=td.sample_folder_path,
        youtube_description=DEFAULT_VIDEO_DESCRIPTION,
        youtube_title=td.sample_video_title,
        youtube_client=mock_youtube_auth(),
    )
    return uploader


def test_YouTubeUpload_initializes_correctly_with_logger(mock_logger: MagicMock):
    # Arrange
    mock_uploader = YouTubeUpload(
        logger=mock_logger,
        source_directory=td.sample_folder_path,
        youtube_description=DEFAULT_VIDEO_DESCRIPTION,
        youtube_title=td.sample_video_title,
        youtube_client=mock_youtube_auth(),
    )

    # Act & Assert
    assert isinstance(mock_uploader.youtube, YouTubeAuth)
    assert mock_uploader.youtube_description == DEFAULT_VIDEO_DESCRIPTION
    assert mock_uploader.youtube_title == td.sample_video_title
    assert mock_uploader.source_directory == td.sample_folder_path
    assert mock_uploader.logger
    assert mock_uploader.input_file_extensions == [MP4_FILE]
    assert mock_uploader.privacy_status == VideoPrivacyStatus.PUBLIC.value
    assert mock_uploader.youtube_category_id == YOUTUBE_MUSIC_CATEGORY
    assert mock_uploader.youtube_keywords == YOUTUBE_KEYWORDS


def test_YouTubeUpload_default_logger_initializes_correctly():
    # Arrange
    mock_uploader = YouTubeUpload(
        source_directory=td.sample_folder_path,
        youtube_description=DEFAULT_VIDEO_DESCRIPTION,
        youtube_title=td.sample_video_title,
        youtube_client=mock_youtube_auth(),
    )

    # Act & Assert
    assert isinstance(mock_uploader.youtube, YouTubeAuth)
    assert isinstance(mock_uploader.logger, Logger)
    assert mock_uploader.logger.hasHandlers()
    assert mock_uploader.logger.name == "YouTubeUploader"
    assert mock_uploader.youtube_description == DEFAULT_VIDEO_DESCRIPTION
    assert mock_uploader.youtube_title == td.sample_video_title
    assert mock_uploader.source_directory == td.sample_folder_path
    assert mock_uploader.input_file_extensions == [MP4_FILE]
    assert mock_uploader.privacy_status == VideoPrivacyStatus.PUBLIC.value
    assert mock_uploader.youtube_category_id == YOUTUBE_MUSIC_CATEGORY
    assert mock_uploader.youtube_keywords == YOUTUBE_KEYWORDS


def test_find_input_files_raises_Exception_if_no_files_found(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange
    with patch(
        "src.automatic_time_lapse_creator.youtube_manager.os.listdir",
        return_value=[],
    ):
        # Act
        result = mock_uploader.find_input_files()

    # Assert
    assert result == []
    mock_logger.error.assert_called_once()
    assert mock_logger.info.call_count == 0


def test_find_input_files_raises_Exception_if_folder_contains_invalid_files(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.youtube_manager.os.listdir",
        return_value=[td.invalid_json_content],
    ):
        assert not mock_uploader.find_input_files()
        mock_logger.error.assert_called_once()


def test_find_input_files_returns_list_with_files(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange
    expected = [os.path.join(mock_uploader.source_directory, td.sample_video_file1)]

    # Act
    with patch(
        "src.automatic_time_lapse_creator.youtube_manager.os.listdir",
        return_value=[td.sample_video_file1],
    ):
        actual_result = mock_uploader.find_input_files()

        # Assert
        assert expected == actual_result
        mock_logger.info.assert_called_once_with(
            f"Found {len(expected)} video files to upload."
        )


def test_shorten_title_within_limit(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange
    title = td.sample_video_title
    max_length = len(title) + 1

    # Act
    result = mock_uploader.shorten_title(title, max_length)

    # Assert
    assert result == title
    mock_logger.debug.assert_not_called()


def test_shorten_title_exceeds_limit(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange
    title = td.sample_video_title
    max_length = len(title) - 1

    # Act
    result = mock_uploader.shorten_title(title, max_length)

    # Assert
    expected = "Sample Video ..."
    assert result == expected
    mock_logger.debug.assert_called_once_with(
        f"Truncating title with length {len(title)} to: {expected}"
    )


def test_shorten_title_exact_boundary(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange
    title = td.sample_video_title
    max_length = len(title)

    # Act
    result = mock_uploader.shorten_title(title, max_length)

    # Assert
    assert result == title
    mock_logger.debug.assert_not_called()


def test_upload_video_to_youtube_actual_upload(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.MediaFileUpload"
        ) as mock_media_file,
        patch.object(
            mock_uploader.youtube.service.videos().insert(),
            "next_chunk",
            side_effect=[(None, td.mock_mediaFileUpload_response)],
        ) as mock_next_chunk,
    ):
        result = mock_uploader.upload_video_to_youtube(
            td.sample_video_file1,
            td.sample_video_title,
            DEFAULT_VIDEO_DESCRIPTION,
        )

        # Assert
        assert result == td.sample_video_id
        mock_media_file.assert_called_once_with(
            td.sample_video_file1, resumable=True, chunksize=DEFAULT_CHUNK_SIZE
        )
        mock_next_chunk.assert_called_once()
        mock_logger.info.assert_any_call(
            f"Uploaded video to YouTube: {YOUTUBE_URL_PREFIX}{td.sample_video_id}"
        )


def test_upload_video_to_youtube_raises_HttpLib2Error(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.MediaFileUpload"
        ) as mock_media_file,
        patch.object(
            mock_uploader.youtube.service.videos().insert(),
            "next_chunk",
            side_effect=HttpLib2Error,
        ) as mock_next_chunk,
    ):
        # Act & Assert
        with pytest.raises(HttpLib2Error):
            mock_uploader.upload_video_to_youtube(
                td.sample_video_file1,
                td.sample_video_title,
                DEFAULT_VIDEO_DESCRIPTION,
            )

        mock_media_file.assert_called_once()
        mock_next_chunk.assert_called_once()
        mock_logger.info.assert_called_once()


def test_process_uploads_videos_successfully(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange & Act
    with (
        patch.object(
            mock_uploader,
            "find_input_files",
            return_value=[td.sample_video_file1],
        ) as mock_find,
        patch.object(
            mock_uploader,
            "upload_video_to_youtube",
            return_value=td.sample_video_id,
        ) as mock_upload,
    ):
        result = mock_uploader.process()

        # Assert
        expected_result = {
            "youtube_title": td.sample_video_title,
            "youtube_id": td.sample_video_id,
        }

        assert result == expected_result
        mock_find.assert_called_once()
        mock_upload.assert_called_once_with(
            td.sample_video_file1,
            td.sample_video_title,
            DEFAULT_VIDEO_DESCRIPTION,
        )
        mock_logger.assert_not_called()

def test_process_logs_error_if_Exception_occurs_during_upload(
    mock_uploader: YouTubeUpload, mock_logger: MagicMock
):
    # Arrange & Act
    with (
        patch.object(
            mock_uploader,
            "find_input_files",
            return_value=[td.sample_video_file1],
        ) as mock_find,
        patch.object(
            mock_uploader,
            "upload_video_to_youtube",
            side_effect=Exception,
        ) as mock_upload,
    ):
        result = mock_uploader.process()

        # Assert
        expected_result = {}

        mock_find.assert_called_once()
        mock_upload.assert_called_once_with(
            td.sample_video_file1,
            td.sample_video_title,
            DEFAULT_VIDEO_DESCRIPTION,
        )
        mock_logger.error.assert_called_once()
        assert result == expected_result
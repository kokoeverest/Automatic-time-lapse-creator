import logging
from unittest.mock import MagicMock, mock_open, patch

import pytest
import tests.test_data as td
from src.automatic_time_lapse_creator.youtube_manager import YouTubeAuth
from src.automatic_time_lapse_creator.common.constants import AuthMethod


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=logging.Logger)
    yield mock_logger
    mock_logger.reset_mock()


def test_validate_secrets_file_valid(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.isfile", return_value=True),
    ):
        assert not YouTubeAuth.validate_secrets_file(mock_logger, td.mock_secrets_file)


def test_validate_secrets_file_invalid_json(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("builtins.open", mock_open(read_data=td.invalid_json_content)),
        patch("os.path.isfile", return_value=True),
    ):
        with pytest.raises(Exception):
            result = YouTubeAuth.validate_secrets_file(
                mock_logger, td.mock_secrets_file
            )
            assert result == "YouTube client secrets file is not valid JSON"
            mock_logger.assert_called_once()


def test_validate_secrets_file_missing_file(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with patch("os.path.isfile", return_value=False):
        with pytest.raises(FileNotFoundError):
            result = YouTubeAuth.validate_secrets_file(
                mock_logger, td.mock_secrets_file
            )
            assert result == "YouTube client secrets file does not exist"


def test_authenticate_youtube_with_valid_token(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data="mock_token_data")),
        patch("pickle.load", return_value=MagicMock(valid=True)),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        result = YouTubeAuth.authenticate_youtube(mock_logger, td.mock_secrets_file, AuthMethod.MANUAL)
        assert result == "YouTubeService"


def test_authenticate_youtube_with_new_auth(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("os.path.exists", return_value=False),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.YouTubeAuth.open_browser_to_authenticate",
            return_value=MagicMock(),
        ),
        patch("pickle.dump"),
        patch("builtins.open", mock_open()),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        result = YouTubeAuth.authenticate_youtube(mock_logger, td.mock_secrets_file, AuthMethod.MANUAL)
        assert result == "YouTubeService"

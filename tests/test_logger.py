import logging
from queue import Queue
from logging.handlers import TimedRotatingFileHandler, QueueHandler
from typing import Any
from unittest.mock import patch, MagicMock
import pytest

from src.automatic_time_lapse_creator.common.logger import configure_root_logger, configure_child_logger

@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_logger.handlers = []
    yield mock_logger
    mock_logger.reset_mock()

def test_configure_root_logger_creates_logger_with_default_settings():
    # Arrange
    logger = logging.getLogger("__root__")
    logger.handlers.clear()

    with (
        patch("logging.basicConfig"),
        patch("pathlib.Path.mkdir"),
        patch("logging.handlers.TimedRotatingFileHandler.__init__", return_value=None),
    ):
        # Act
        logger = configure_root_logger()

    # Assert
    assert isinstance(logger, logging.Logger)
    assert logger.name == "__root__"
    assert len(logger.handlers) == 2
    assert any(not isinstance(handler, QueueHandler) for handler in logger.handlers)
    
    for handler in logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            assert handler.level == logging.DEBUG
        elif isinstance(handler, logging.StreamHandler):
            assert handler.level == logging.INFO


def test_configure_root_logger_with_custom_logger_name():
    # Arrange
    with patch("logging.getLogger", return_value=logging.getLogger("custom_logger")):
        # Act
        logger = configure_root_logger(logger_name="custom_logger")

    # Assert
    assert logger.name == "custom_logger"


def test_configure_root_logger_with_log_queue():
    # Arrange
    mock_queue = Queue[Any]()

    with (
        patch("logging.getLogger", return_value=logging.getLogger("queue_logger")),
        patch("logging.handlers.QueueHandler", return_value=MagicMock()),
    ):
        # Act
        logger = configure_root_logger(log_queue=mock_queue)

    # Assert
    assert len(logger.handlers) == 1
    assert any(isinstance(handler, QueueHandler) for handler in logger.handlers)
    assert any(
        not isinstance(handler, TimedRotatingFileHandler) for handler in logger.handlers
    )
    assert logger.handlers[0].level == logging.DEBUG
    assert len(logger.handlers) == 1


def test_configure_root_logger_creates_logs_directory():
    # Arrange
    with (
        patch("logging.basicConfig"),
        patch("pathlib.Path.mkdir") as mock_mkdir,
        patch("logging.handlers.TimedRotatingFileHandler.__init__", return_value=None),
    ):
        # Act
        logger = configure_root_logger(logger_base_path="test_path")

    # Assert
    mock_mkdir.assert_called_once()
    assert logger is not None


def test_configure_root_logger_suppresses_urllib3_debug_logs():
    # Arrange
    with (
        patch("logging.basicConfig"),
        patch("pathlib.Path.mkdir"),
        patch("logging.handlers.TimedRotatingFileHandler.__init__", return_value=None),
        patch("logging.getLogger", return_value=logging.getLogger("urllib3")),
    ):
        # Act
        _ = configure_root_logger()

    # Assert
    urllib3_logger = logging.getLogger("urllib3")
    assert urllib3_logger.level == logging.INFO


def test_configure_child_logger_returns_the_same_logger_if_not_None_and_has_handler(
        mock_logger: logging.Logger
):
    # Arrange
    mock_handler = MagicMock(spec=logging.StreamHandler)
    mock_logger.addHandler(mock_handler)

    # Act
    actual_result = configure_child_logger("", mock_logger)

    # Assert
    assert actual_result is mock_logger
    assert actual_result.hasHandlers()


def test_configure_child_logger_returns_the_same_logger_with_new_handler():
    logger = logging.getLogger("fake logger")
    # Arrang 
    with (
        patch.object(logger, "hasHandlers", return_value= False),
        patch("logging.StreamHandler.__init__", return_value=None),
    ):
        # Act
        actual_result = configure_child_logger("", logger)

    # Assert
    assert actual_result is logger
    assert actual_result.hasHandlers()
    for handler in actual_result.handlers:
        assert isinstance(handler, logging.StreamHandler)


def test_configure_child_logger_returns_new_logger_with_new_handler(mock_logger: logging.Logger):
    # Arrange
    logger = None
    logger_name = "new logger"
    
    with (
        patch("logging.getLogger", return_value= mock_logger),
        patch("logging.StreamHandler.__init__", return_value=None),
    ):
        # Act
        actual_result = configure_child_logger(logger_name, logger)

    # Assert
    assert actual_result is not None
    assert actual_result.hasHandlers()
    for handler in actual_result.handlers:
        assert isinstance(handler, logging.StreamHandler)
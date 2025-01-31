from unittest.mock import mock_open, patch
import pytest

from src.automatic_time_lapse_creator.cache_manager import (
    CacheManager,
)
from src.automatic_time_lapse_creator.time_lapse_creator import (
    TimeLapseCreator,
)
import tests.test_data as td


@pytest.fixture
def sample_non_empty_time_lapse_creator():
    return TimeLapseCreator([td.sample_source_no_weather_data, td.sample_source2_no_weather_data, td.sample_source3_no_weather_data])


def test_write_returns_none_after_writing_to_file(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    mock_file = mock_open()

    # Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.cache_manager.Path.mkdir",
            return_value=None,
        ),
        patch("src.automatic_time_lapse_creator.cache_manager.Path.open", mock_file),
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert not CacheManager.write(
                logger=sample_non_empty_time_lapse_creator.logger,
                time_lapse_creator=sample_non_empty_time_lapse_creator,
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
                quiet=False,
            )
        assert mock_logger.call_count == 3


def test_get_returns_TimeLapsCreator_object(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    mock_creator = TimeLapseCreator([td.sample_source_no_weather_data])
    mock_file = mock_open()

    # Act & Assert
    with (
        patch("src.automatic_time_lapse_creator.cache_manager.Path.open", mock_file),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.Path.exists",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.pickle.load",
            return_value=mock_creator,
        ),
        patch("src.automatic_time_lapse_creator.cache_manager.Path.open", mock_file),
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "debug", return_value=None
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            result = CacheManager.get(
                logger=sample_non_empty_time_lapse_creator.logger,
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
            )
            assert isinstance(result, TimeLapseCreator)
        assert mock_logger.call_count == (
            len(sample_non_empty_time_lapse_creator.sources) * 2
        )


def test_get_returns_FileNotFoundError_if_the_file_doesnt_exist(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.cache_manager.Path.exists",
            return_value=False,
        ),
        patch.object(
            sample_non_empty_time_lapse_creator, "logger", return_value=None
        ) as mock_logger,
    ):
        with pytest.raises(FileNotFoundError):
            for source in sample_non_empty_time_lapse_creator.sources:
                result = CacheManager.get(
                    logger=sample_non_empty_time_lapse_creator.logger,
                    location=source.location_name,
                    path_prefix=sample_non_empty_time_lapse_creator.base_path,
                )
                assert isinstance(result, FileNotFoundError)

        assert mock_logger.debug.call_count == 1
        assert mock_logger.warning.call_count == 1


def test_clear_cache_logs_warning_if_file_not_found(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.cache_manager.Path.exists",
            return_value=False,
        ),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.os.remove",
            return_value=None,
        ) as mock_remove,
        patch.object(
            sample_non_empty_time_lapse_creator, "logger", return_value=None
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            result = CacheManager.clear_cache(
                logger=sample_non_empty_time_lapse_creator.logger,
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
            )
            assert not result
        assert mock_remove.call_count == 0
        assert mock_logger.debug.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )
        assert mock_logger.warning.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )


def test_clear_cache_removes_the_file(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.cache_manager.Path.exists",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.os.remove",
            return_value=None,
        ) as mock_remove,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "debug", return_value=None
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            result = CacheManager.clear_cache(
                logger=sample_non_empty_time_lapse_creator.logger,
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
            )
            assert not result
        assert mock_remove.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )
        assert mock_logger.call_count == (
            len(sample_non_empty_time_lapse_creator.sources) * 2
        )

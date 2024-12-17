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
    return TimeLapseCreator([td.sample_source1, td.sample_source2, td.sample_source3])


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
        patch(
            "src.automatic_time_lapse_creator.cache_manager.logger.info",
            return_value=None,
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert not CacheManager.write(
                sample_non_empty_time_lapse_creator,
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
            )
        assert mock_logger.call_count == 3


def test_get_returns_TimeLapsCreator_object(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    mock_creator = TimeLapseCreator([td.sample_source1])
    mock_file = mock_open()

    # Act & Assert
    with (
        patch("src.automatic_time_lapse_creator.cache_manager.Path.open", mock_file),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.pickle.load",
            return_value=mock_creator,
        ),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.logger.info",
            return_value=None,
        ) as mock_logger,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            result = CacheManager.get(
                location=source.location_name,
                path_prefix=sample_non_empty_time_lapse_creator.base_path,
            )
            assert isinstance(result, TimeLapseCreator)
        assert mock_logger.call_count == 3
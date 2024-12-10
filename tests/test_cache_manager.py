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
    with patch("builtins.open", mock_file):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert not CacheManager.write(
                sample_non_empty_time_lapse_creator, source.location_name
            )


def test_get_returns_TimeLapsCreator_object(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    mock_creator = TimeLapseCreator([td.sample_source1])
    mock_file = mock_open()

    # Act & Assert
    with (
        patch("builtins.open", mock_file),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.pickle.load",
            return_value=mock_creator,
        ),
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            result = CacheManager.get(source.location_name)
            assert isinstance(result, TimeLapseCreator)

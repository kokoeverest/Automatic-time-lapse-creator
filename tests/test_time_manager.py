from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock
from astral import LocationInfo
from logging import Logger
from src.automatic_time_lapse_creator.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator.common.exceptions import (
    UnknownLocationException,
)
from src.automatic_time_lapse_creator.common.constants import (
    DEFAULT_CITY_NAME,
    DEFAULT_SUNSET_OFFSET,
    DEFAULT_SUNRISE_OFFSET,
)
import tests.test_data as td
import tests.test_mocks as tm


logger = MagicMock(spec=Logger)


@pytest.fixture
def sample_LocationAndTimeManager():
    return LocationAndTimeManager(
        city_name=DEFAULT_CITY_NAME,
        sunrise_offset=DEFAULT_SUNRISE_OFFSET,
        sunset_offset=DEFAULT_SUNSET_OFFSET,
        logger=logger,
    )


def test_LocationAndTimeManager_raises_UnknownLocationException_if_city_is_not_found(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch.object(
        sample_LocationAndTimeManager.logger, "error", return_value=None
    ) as mock_logger:
        with pytest.raises(UnknownLocationException):
            LocationAndTimeManager(
                city_name=td.invalid_city_name,
                sunrise_offset=DEFAULT_SUNRISE_OFFSET,
                sunset_offset=DEFAULT_SUNSET_OFFSET,
                logger=logger,
            )
        assert mock_logger.call_count == 1


def test_LocationAndTimeManager_raises_NotImplementedError_if_city_is_a_GroupInfo_object(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch.object(
        sample_LocationAndTimeManager.logger, "warning", return_value=None
    ) as mock_logger:
        with pytest.raises(NotImplementedError):
            LocationAndTimeManager(
                city_name=td.group_name,
                sunrise_offset=DEFAULT_SUNRISE_OFFSET,
                sunset_offset=DEFAULT_SUNSET_OFFSET,
                logger=logger,
            )
        assert mock_logger.call_count == 1


def test_LocationAndTimeManager_initializes_correctly_for_correct_location(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    assert isinstance(sample_LocationAndTimeManager, LocationAndTimeManager)
    assert isinstance(sample_LocationAndTimeManager.db, dict)
    assert isinstance(sample_LocationAndTimeManager.city, LocationInfo)
    assert isinstance(sample_LocationAndTimeManager.start_of_daylight, datetime)
    assert isinstance(sample_LocationAndTimeManager.end_of_daylight, datetime)

    for attr in [
        sample_LocationAndTimeManager.year,
        sample_LocationAndTimeManager.month,
        sample_LocationAndTimeManager.today,
    ]:
        assert isinstance(attr, int)


def test_is_daylight_returns_True_during_the_day(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch("src.automatic_time_lapse_creator.time_manager.dt") as mock_datetime:
        mock_datetime.now.return_value = tm.MockDatetime.fake_daylight
        result = sample_LocationAndTimeManager.is_daylight()

        assert isinstance(result, bool)
        assert result is True


def test_is_daylight_returns_False_during_the_night(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch("src.automatic_time_lapse_creator.time_manager.dt") as mock_datetime:
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        result = sample_LocationAndTimeManager.is_daylight()

        assert isinstance(result, bool)
        assert result is not True

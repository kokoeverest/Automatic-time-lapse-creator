from datetime import datetime, timedelta
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
    DEFAULT_SUNSET_OFFSET_MINUTES,
    DEFAULT_SUNRISE_OFFSET_MINUTES,
    SUNSET_OFFSET_VALIDATION_RANGE,
    SUNRISE_OFFSET_VALIDATION_RANGE,
)
import tests.test_data as td
import tests.test_mocks as tm


logger = MagicMock(spec=Logger)


@pytest.fixture
def sample_LocationAndTimeManager():
    return LocationAndTimeManager(
        city_name=DEFAULT_CITY_NAME,
        sunrise_offset=DEFAULT_SUNRISE_OFFSET_MINUTES,
        sunset_offset=DEFAULT_SUNSET_OFFSET_MINUTES,
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
                sunrise_offset=DEFAULT_SUNRISE_OFFSET_MINUTES,
                sunset_offset=DEFAULT_SUNSET_OFFSET_MINUTES,
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
                sunrise_offset=DEFAULT_SUNRISE_OFFSET_MINUTES,
                sunset_offset=DEFAULT_SUNSET_OFFSET_MINUTES,
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


def test_is_daylight_returns_False_at_midnight_in_the_longest_day_of_the_year_with_max_offsets(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    """
    This test evaluates that even in the longest day of the year and with 
    maximum sunrise and sunset offsets, the is_daylight function will work properly.
    This ensures that there will be a time interval during the day when photos will 
    not be collected and there will be enough time for the creation of a video
    (having in mind the current implementation, without using async methods)...
    """
    # Arrange
    max_sunrise_offset_minutes = max(SUNRISE_OFFSET_VALIDATION_RANGE)
    max_sunset_offset_minutes = max(SUNSET_OFFSET_VALIDATION_RANGE)
    sample_LocationAndTimeManager.sunrise_offset_minutes = timedelta(minutes=max_sunrise_offset_minutes)
    sample_LocationAndTimeManager.sunset_offset_minutes = timedelta(minutes=max_sunset_offset_minutes)

    _ =  tm.MockDatetime.fake_longest_day_of_the_year
    fake_time_with_current_tz_info = datetime(
        year=_.year,
        month=_.month, 
        day=_.day, 
        hour=_.hour, 
        minute=_.minute, 
        second=_.second, 
        tzinfo=sample_LocationAndTimeManager.city.tzinfo # type: ignore
        )
    
    # Act & Assert
    with patch("src.automatic_time_lapse_creator.time_manager.dt") as mock_datetime:
        mock_datetime.now.return_value = fake_time_with_current_tz_info
        result = sample_LocationAndTimeManager.is_daylight()

        assert isinstance(result, bool)
        assert result is not True

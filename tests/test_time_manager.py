from datetime import datetime
import pytest
from unittest.mock import patch
from astral import LocationInfo
from src.automatic_time_lapse_creator.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator.common.exceptions import (
    UnknownLocationException,
)
from src.automatic_time_lapse_creator.common.constants import (
    DEFAULT_CITY_NAME,
)
import tests.test_data as td
import tests.test_mocks as tm


@pytest.fixture
def sample_LocationAndTimeManager():
    return LocationAndTimeManager(DEFAULT_CITY_NAME)


def test_LocationAndTimeManager_raises_UnknownLocationException_if_city_is_not_found():
    # Arrange, Act & Assert
    with pytest.raises(UnknownLocationException):
        LocationAndTimeManager(td.invalid_city_name)


def test_LocationAndTimeManager_initializes_correctly_for_correct_location(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    assert isinstance(sample_LocationAndTimeManager, LocationAndTimeManager)
    assert isinstance(sample_LocationAndTimeManager.db, dict)
    assert isinstance(sample_LocationAndTimeManager.city_is_location_info_object, bool)
    assert isinstance(sample_LocationAndTimeManager.city, LocationInfo)

    for attr in (
        sample_LocationAndTimeManager.start_hour,
        sample_LocationAndTimeManager.start_minutes,
        sample_LocationAndTimeManager.end_hour,
        sample_LocationAndTimeManager.end_minutes,
    ):
        assert isinstance(attr, int)

    for attr in (
        sample_LocationAndTimeManager.start_of_daylight,
        sample_LocationAndTimeManager.end_of_daylight,
    ):
        assert isinstance(attr, datetime)


def test_s_rise_returns_tuple_with_two_integers(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange
    actual_result = sample_LocationAndTimeManager.s_rise()

    # Act & Assert
    assert isinstance(actual_result, tuple)
    assert len(actual_result) == 2
    assert all(isinstance(x, int) for x in actual_result)


def test_s_set_returns_tuple_with_two_integers(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange
    actual_result = sample_LocationAndTimeManager.s_set()

    # Act & Assert
    assert isinstance(actual_result, tuple)
    assert len(actual_result) == 2
    assert all(isinstance(x, int) for x in actual_result)


def test_is_daylight_returns_True_during_the_day(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.time_manager.dt"
    ) as mock_datetime:
        mock_datetime.now.return_value = tm.MockDatetime.fake_daylight
        result = sample_LocationAndTimeManager.is_daylight()

        assert isinstance(result, bool)
        assert result is True


def test_is_daylight_returns_False_during_the_night(
    sample_LocationAndTimeManager: LocationAndTimeManager,
):
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.time_manager.dt"
    ) as mock_datetime:
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        result = sample_LocationAndTimeManager.is_daylight()

        assert isinstance(result, bool)
        assert result is not True

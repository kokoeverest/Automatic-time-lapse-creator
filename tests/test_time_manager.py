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


def test_LocationAndTimeManager_raises_NotImplementedError_if_city_is_a_GroupInfo_object():
    # Arrange, Act & Assert
    with pytest.raises(NotImplementedError):
        LocationAndTimeManager(td.group_name)


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

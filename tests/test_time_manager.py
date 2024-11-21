import pytest
from src.automatic_time_lapse_creator_kokoeverest.time_manager import LocationAndTimeManager
from src.automatic_time_lapse_creator_kokoeverest.common.exceptions import UnknownLocationException
import tests.test_data as td



@pytest.fixture
def sample_LocationAndTimeManager():
    return LocationAndTimeManager(td.default_city_name)


def test_LocationAndTimeManager_raises_UnknownLocationException_if_city_is_not_found():
    with pytest.raises(UnknownLocationException):
        LocationAndTimeManager(td.invalid_city_name)
from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from astral import LocationInfo
from datetime import datetime as dt, timedelta as td
import logging

from src.automatic_time_lapse_creator_kokoeverest.common.exceptions import (
    UnknownLocationException,
)

logger = logging.getLogger(__name__)

class LocationAndTimeManager:
    """"""

    YEAR, MONTH, TODAY = dt.today().year, dt.today().month, dt.today().day

    def __init__(self, city_name: str) -> None:
        self.db = database()

        try:
            self.city = lookup(city_name, self.db)
        except KeyError:
            UNKNOWN_LOCATION_MESSAGE = (
                f"Location could not be found. "
                f"Try to use a major city name in your area."
            )
            logger.error(UNKNOWN_LOCATION_MESSAGE, exc_info=True)
            raise UnknownLocationException(UNKNOWN_LOCATION_MESSAGE)

        if self.city_is_location_info_object:
            self.start_hour, self.start_minutes = self.s_rise()
            self.end_hour, self.end_minutes = self.s_set()
        else:
            NOT_IMPLEMENTED_MESSAGE = "Sunset and sunrise for GroupInfo not implemented yet"
            logger.warning(NOT_IMPLEMENTED_MESSAGE, exc_info=True)
            raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

        self.start_of_daylight = dt(
            year=LocationAndTimeManager.YEAR,
            month=LocationAndTimeManager.MONTH,
            day=LocationAndTimeManager.TODAY,
            hour=self.start_hour,
            minute=self.start_minutes,
        )

        self.end_of_daylight = dt(
            year=LocationAndTimeManager.YEAR,
            month=LocationAndTimeManager.MONTH,
            day=LocationAndTimeManager.TODAY,
            hour=self.end_hour,
            minute=self.end_minutes,
        )

    @property
    def city_is_location_info_object(self):
        return isinstance(self.city, LocationInfo)
    
    def s_rise(self):
        """"""
        assert isinstance(self.city, LocationInfo)
        sun_rise = sunrise(self.city.observer) + td(hours=1, minutes=20)
        return sun_rise.hour, sun_rise.minute

    def s_set(self):
        """"""
        assert isinstance(self.city, LocationInfo)
        sun_set = sunset(self.city.observer) + td(hours=2, minutes=40)
        return sun_set.hour, sun_set.minute

    def is_daylight(self):
        """"""

        return self.start_of_daylight < dt.now() < self.end_of_daylight
    
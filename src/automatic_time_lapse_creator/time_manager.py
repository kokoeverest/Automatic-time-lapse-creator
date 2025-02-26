from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from astral import LocationInfo
from datetime import datetime as dt, timedelta as td
import logging
from logging import Logger
from .common.exceptions import (
    UnknownLocationException,
)


class LocationAndTimeManager:
    """Takes care of the sunrise and sunset times for the specified city, which ensures that images are collected only
    while it's daylight. Checks if the current time is within the daylight interval or is it night time. Light offsets
    are added to the sunrise and sunset times so the images would be collected in good light conditions."""


    def __init__(self, city_name: str, sunrise_offset: int, sunset_offset: int, logger: Logger | None = None) -> None:
        self.db = database()
        self.sunrise_offset = td(minutes=sunrise_offset)
        self.sunset_offset = td(minutes=sunset_offset)

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        try:
            _city = lookup(city_name, self.db)
        except KeyError:
            UNKNOWN_LOCATION_MESSAGE = "Location could not be found.\nTry to use a major city name in your area."
            self.logger.error(UNKNOWN_LOCATION_MESSAGE, exc_info=True)
            raise UnknownLocationException(UNKNOWN_LOCATION_MESSAGE)

        if isinstance(_city, LocationInfo):
            self.city = _city
        else:
            NOT_IMPLEMENTED_MESSAGE = f"Sunset and sunrise for {_city} not implemented yet. Use a major city name in the needed timezone."
            self.logger.warning(NOT_IMPLEMENTED_MESSAGE, exc_info=True)
            raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @property
    def start_of_daylight(self) -> dt:
        """Gets the time of sunrise, taking into account that the light is good for taking a picture
        before the actual sunrise time.

        Returns::
            datetime - the datetime object subtracted the self.sunrise_offset minutes"""
        return sunrise(self.city.observer, tzinfo=self.city.tzinfo) - self.sunrise_offset # type: ignore

    @property
    def end_of_daylight(self) -> dt:
        """Gets the time of sunset, taking into account that the light is good for taking a picture
        after the time of sunset.

        Returns::
            datetime - the datetime object plus the self.sunset_offset minutes"""
        return sunset(self.city.observer, tzinfo=self.city.tzinfo) + self.sunset_offset # type: ignore

    @property
    def year(self) -> int:
        """Returns::

        int - current year"""
        return dt.today().year

    @property
    def month(self) -> int:
        """Returns::

        int - current month"""
        return dt.today().month

    @property
    def today(self) -> int:
        """Returns::

        int - current day"""
        return dt.today().day
    
    @property
    def time_now(self):
        """Returns the current date and time taking into account the timezone of the self.city

        Returns:
            datetime: the datetime object representing the current time
        """
        return dt.now(tz=self.city.tzinfo) # type: ignore

    def is_daylight(self) -> bool:
        """Checks if it's daylight at the specified location according to the start and end of daylight.

        Returns::

           bool - if the current time of day is between the start of daylight and end of daylight or not."""
        return self.start_of_daylight < self.time_now < self.end_of_daylight

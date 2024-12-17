from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from astral import LocationInfo
from datetime import datetime as dt, timedelta as td, timezone
import logging
from .common.exceptions import (
    UnknownLocationException,
)
import os
from pathlib import Path
from .common.constants import (
    LOGS_DIR,
    YYMMDD_FORMAT,
    LOG_FILE,
    LOGGING_FORMAT,
    HHMMSS_COLON_FORMAT,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
cwd = os.getcwd()
Path(f"{cwd}{LOGS_DIR}").mkdir(exist_ok=True)
filename = Path(f"{cwd}{LOGS_DIR}/{dt.now().strftime(YYMMDD_FORMAT)}{LOG_FILE}")
date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

logging.basicConfig(filename=filename, datefmt=date_fmt, format=LOGGING_FORMAT)


class LocationAndTimeManager:
    """Takes care of the sunrise and sunset times for the specified city, which ensures that images are collected only
    while it's daylight. Checks if the current time is within the daylight interval or is it night time. Light offsets
    are added to the sunrise and sunset times so the images would be collected in good light conditions."""

    SUNSET_OFFSET = td(minutes=60)
    SUNRISE_OFFSET = td(minutes=40)

    def __init__(self, city_name: str) -> None:
        self.db = database()

        try:
            _city = lookup(city_name, self.db)
        except KeyError:
            UNKNOWN_LOCATION_MESSAGE = "Location could not be found.\nTry to use a major city name in your area."
            logger.error(UNKNOWN_LOCATION_MESSAGE, exc_info=True)
            raise UnknownLocationException(UNKNOWN_LOCATION_MESSAGE)

        if isinstance(_city, LocationInfo):
            self.city = _city
        else:
            NOT_IMPLEMENTED_MESSAGE = f"Sunset and sunrise for {_city} not implemented yet. Use a major city name in the needed timezone."
            logger.warning(NOT_IMPLEMENTED_MESSAGE, exc_info=True)
            raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @property
    def start_of_daylight(self) -> dt:
        """Gets the time of sunrise, taking into account that the light is good for taking a picture
        before the actual sunrise time.

        Returns::
            datetime - the datetime object subtracted the SUNRISE_OFFSET"""
        return sunrise(self.city.observer) - self.SUNRISE_OFFSET

    @property
    def end_of_daylight(self) -> dt:
        """Gets the time of sunset, taking into account that the light is good for taking a picture
        after the time of sunset.

        Returns::
            datetime - the datetime object plus the SUNSET_OFFSET"""
        return sunset(self.city.observer) + self.SUNSET_OFFSET

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

    def is_daylight(self) -> bool:
        """Checks if it's daylight at the specified location according to the start and end of daylight.

        Returns::

           bool - if the current time of day is between the start of daylight and end of daylight or not."""
        return self.start_of_daylight < dt.now(timezone.utc) < self.end_of_daylight

from .common.exceptions import UnknownLocationException as UnknownLocationException
from datetime import datetime, timedelta
from astral import LocationInfo
from logging import Logger


GroupName = str
LocationName = str
GroupInfo = dict[LocationName, list[LocationInfo]]
LocationDatabase = dict[GroupName, GroupInfo]

class LocationAndTimeManager:
    SUNRISE_OFFSET: timedelta
    SUNSET_OFFSET: timedelta
    db: LocationDatabase
    city: LocationInfo
    logger: Logger
    def __init__(self, city_name: str, logger: Logger | None) -> None: ...
    @property
    def start_of_daylight(self) -> datetime: ...
    @property
    def end_of_daylight(self) -> datetime: ...
    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def today(self) -> int: ...
    def is_daylight(self) -> bool: ...

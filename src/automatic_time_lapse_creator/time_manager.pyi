from .common.exceptions import UnknownLocationException as UnknownLocationException
from datetime import datetime, timedelta, _IsoCalendarDate
from astral import LocationInfo
from logging import Logger

GroupName = str
LocationName = str
GroupInfo = dict[LocationName, list[LocationInfo]]
LocationDatabase = dict[GroupName, GroupInfo]

class LocationAndTimeManager:
    sunrise_offset_minutes: timedelta
    sunset_offset_minutes: timedelta
    db: LocationDatabase
    city: LocationInfo
    logger: Logger | None
    def __init__(
        self,
        city_name: str,
        sunrise_offset: int,
        sunset_offset: int,
        logger: Logger | None = ...,
    ) -> None: ...
    @property
    def time_now(self) -> datetime: ...
    @property
    def start_of_daylight(self) -> datetime: ...
    @property
    def end_of_daylight(self) -> datetime: ...
    @property
    def calendar(self) -> _IsoCalendarDate: ...
    def is_daylight(self) -> bool: ...

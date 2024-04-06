from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from datetime import datetime as dt, timedelta as td


class LocationAndTimeManager:
    YEAR, MONTH, TODAY = dt.today().year, dt.today().month, dt.today().day

    def __init__(self, city) -> None:
        self.db = database()
        self.city = lookup(city, self.db)

        self.start_hour, self.start_minutes = self.s_rise()
        self.end_hour, self.end_minutes = self.s_set()

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

    def s_rise(self):
        sun_rise = sunrise(self.city.observer) + td(hours=1, minutes=20)
        return sun_rise.hour, sun_rise.minute

    def s_set(self):
        sun_set = sunset(self.city.observer) + td(hours=2, minutes=40)
        return sun_set.hour, sun_set.minute

    def is_daylight(self):
        return self.start_of_daylight < dt.now() < self.end_of_daylight

# year, month, today = dt.today().year, dt.today().month, dt.today().day

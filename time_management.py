from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from datetime import datetime as dt, timedelta as td

def s_rise():
    sun_rise = sunrise(city.observer) + td(hours=1, minutes=20)
    return sun_rise.hour, sun_rise.minute

def s_set():
    sun_set = sunset(city.observer) + td(hours=2, minutes=40)
    return sun_set.hour, sun_set.minute

def is_daylight():
    return start_of_daylight < dt.now() < end_of_daylight


db = database()
city = lookup('Sofia', db)

year, month, today = dt.today().year, dt.today().month, dt.today().day
start_hour, start_minutes = s_rise()
end_hour, end_minutes = s_set()

start_of_daylight = dt(year=year, month=month, day=today, hour=start_hour, minute=start_minutes)
end_of_daylight = dt(year=year, month=month, day=today, hour=end_hour, minute=end_minutes)

from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset
from datetime import datetime as dt

def s_rise():
    return sunrise(city.observer).hour + 1, sunrise(city.observer).minute

def s_set():
    return sunset(city.observer).hour + 2, sunset(city.observer).minute

def is_daylight():
    return start_of_daylight < dt.now() < end_of_daylight


db = database()
city = lookup('Sofia', db)

year, month, today = dt.today().year, dt.today().month, dt.today().day
start_hour, start_minutes = s_rise()
end_hour, end_minutes = s_set()

start_of_daylight = dt(year=year, month=month, day=today, hour=start_hour, minute=start_minutes)
end_of_daylight = dt(year=year, month=month, day=today, hour=end_hour, minute=end_minutes)

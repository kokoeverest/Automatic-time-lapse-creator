from astral.geocoder import database, lookup
from astral.sun import sunrise, sunset

db = database()
city = lookup('Sofia', db)

def s_rise():
    return sunrise(city.observer).hour + 1, sunrise(city.observer).minute

def s_set():
    return sunset(city.observer).hour + 2, sunset(city.observer).minute
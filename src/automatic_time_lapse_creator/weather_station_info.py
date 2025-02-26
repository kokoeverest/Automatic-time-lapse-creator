from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any
from .common.constants import OLD_TIMESTAMP_HOURS

import requests


class WeatherStationInfo(ABC):
    """
    Abstract base class for retrieving weather data from a weather station.

    The temperature and wind speed formats are set to Celsius (C) and m/s by default and can be
    changed at __init__ .

    #### Note that the degrees symbol ° is not supported by the cv2 font and will be visualised as ?? on the images!

    Abstract method get_data() should be implemented to set the values of the properties:
        - temperature
        - wind_speed_avg
        - wind_speed_gust
        - wind_direction

    Otherwise, these values will be None by default
    """

    def __init__(
        self, url: str, temperature_format: str = "C", wind_speed_format: str = "m/s"
    ) -> None:
        """
        Initialize the weather station info object with a data source URL.
        Wind directions can be provided as a number between 0-360 or as a string with up to 3 letters length
        (N, SE, E, WSW) etc. case insensitive.

        Args:
            url: str - The URL from which weather data will be fetched.
            temperature_format: str - Celsius or Fahrenheit, defaults to "C",
            wind_speed_format: str - m/s or km/h, defaults to "m/s"
        """
        self.url = url
        self.temp_format = temperature_format
        self.wind_speed_format = wind_speed_format
        self._temperature: float | None = None
        self._wind_speed_avg: float | None = None
        self._wind_speed_gust: float | None = None
        self._wind_direction: float | str | None = None

    @abstractmethod
    def get_data(self) -> None:
        """Fetches weather data from the specified URL and sets the internal properties."""
        pass

    @property
    def temperature(self) -> float | None:
        """Returns the temperature in degrees Celsius."""
        return self._temperature

    @temperature.setter
    def temperature(self, value: float | None) -> None:
        """Sets the temperature, ensuring it is stored as a float."""
        self._temperature = self._parse_float(value)

    @property
    def wind_speed_avg(self) -> float | None:
        """Returns the average wind speed in m/s."""
        return self._wind_speed_avg

    @wind_speed_avg.setter
    def wind_speed_avg(self, value: float | None) -> None:
        """Sets the average wind speed, ensuring it is stored as a float."""
        self._wind_speed_avg = self._parse_float(value)

    @property
    def wind_speed_gust(self) -> float | None:
        """Returns the gust wind speed in m/s."""
        return self._wind_speed_gust

    @wind_speed_gust.setter
    def wind_speed_gust(self, value: float | None) -> None:
        """Sets the gust wind speed, ensuring it is stored as a float."""
        self._wind_speed_gust = self._parse_float(value)

    @property
    def wind_direction(self) -> float | str | None:
        """Returns the wind direction in degrees (0-360) or letters (N, S, E, W) etc."""
        return self._wind_direction

    @wind_direction.setter
    def wind_direction(self, value: float | str | None) -> None:
        """Sets the wind direction, ensuring it is stored as a float, str or None if it's invalid"""
        if isinstance(value, str) and 0 < len(value) <= 3 and value.isalpha():
            self._wind_direction = value
        else:
            _val = self._parse_float(value)

            if _val is not None and 0 <= _val <= 360:
                self._wind_direction = _val
            else:
                self._wind_direction = None

    @staticmethod
    def _parse_float(value: float | str | None) -> float | None:
        """Helper method to parse a value as a float, handling None and empty strings."""
        try:
            return float(value) if value is not None and value != "" else None
        except ValueError:
            return None

    def __str__(self) -> str:
        """Returns a formatted string representation of the weather data."""
        temp_text = (
            f"{self.temperature:.1f} {self.temp_format}"
            if self.temperature is not None
            else "-"
        )
        wind_avg_text = (
            f"{self.wind_speed_avg:.1f} {self.wind_speed_format}"
            if self.wind_speed_avg is not None
            else "-"
        )
        wind_gust_text = (
            f"{self.wind_speed_gust:.1f} {self.wind_speed_format}"
            if self.wind_speed_gust is not None
            else "-"
        )

        if isinstance(self.wind_direction, str):
            wind_dir_text = self.wind_direction
        elif isinstance(self.wind_direction, float):
            wind_dir_text = self._get_wind_direction(self.wind_direction)
        else:
            wind_dir_text = "-"

        return f"Temp: {temp_text} | Wind: {wind_avg_text} {wind_dir_text} (Gust: {wind_gust_text})"

    @staticmethod
    def _get_wind_direction(degrees: float) -> str:
        """Converts a wind direction in degrees to a cardinal direction."""
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        idx = round(degrees / 22.5) % 16  # 360° / 16 = 22.5° per section
        return directions[idx]


class MeteoRocks(WeatherStationInfo):
    def get_data(self) -> None:
        """Fetches weather data from the meteo.rocks API and updates internal properties."""
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            stamp = data.get("timestamp")
            assert stamp
            time_stamp = datetime.fromtimestamp(float(stamp))
            last_record = datetime.now() - time_stamp

            if last_record < timedelta(hours=OLD_TIMESTAMP_HOURS):
                self.temperature = data.get("temp")
                self.wind_speed_avg = data.get("windspeed_average")
                self.wind_speed_gust = data.get("windspeed_gust")
                self.wind_direction = data.get("winddirection")

        except (requests.RequestException, ValueError) as e:
            print(f"Failed to fetch weather data: {e}")

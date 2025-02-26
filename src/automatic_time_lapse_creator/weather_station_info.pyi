from abc import ABC, abstractmethod

class WeatherStationInfo(ABC):
    url: str
    temp_format: str
    wind_speed_format: str
    def __init__(
        self, url: str, temperature_format: str = ..., wind_speed_format: str = ...
    ) -> None: ...
    @abstractmethod
    def get_data(self) -> None: ...
    @property
    def temperature(self) -> float | None: ...
    @temperature.setter
    def temperature(self, value: float | str | None) -> None: ...
    @property
    def wind_speed_avg(self) -> float | None: ...
    @wind_speed_avg.setter
    def wind_speed_avg(self, value: float | str | None) -> None: ...
    @property
    def wind_speed_gust(self) -> float | None: ...
    @wind_speed_gust.setter
    def wind_speed_gust(self, value: float | str | None) -> None: ...
    @property
    def wind_direction(self) -> float | None: ...
    @wind_direction.setter
    def wind_direction(self, value: float | str | None) -> None: ...
    def __str__(self) -> str: ...

class MeteoRocks(WeatherStationInfo):
    def get_data(self) -> None: ...

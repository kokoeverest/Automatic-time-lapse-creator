import pytest
from unittest.mock import Mock, patch
from typing import Any

from requests import Response, RequestException
from src.automatic_time_lapse_creator.common.constants import (
    OK_STATUS_CODE,
    OLD_TIMESTAMP_HOURS,
)
from src.automatic_time_lapse_creator.weather_station_info import (
    WeatherStationInfo,
    MeteoRocks,
)
import tests.test_data as td
from datetime import datetime, timedelta


def mock_api_return(
    timestamp: float = datetime.now().timestamp(),
    temp: float = -1,
    wind_avg: float = 8.2,
    wind_gust: float = 12,
    wind_dir: str | float = 181,
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "temp": temp,
        "windspeed_average": wind_avg,
        "windspeed_gust": wind_gust,
        "winddirection": wind_dir,
    }


def response_generator(content: dict[str, Any] = mock_api_return()):
    response = Mock(spec=Response)
    response.status_code = OK_STATUS_CODE
    response.content = content
    response.raise_for_status.return_value = None
    response.json.return_value = content
    return response


@pytest.fixture
def mock_weather_station_info():
    mock_url = td.valid_url
    meteo_rocks_mock = MeteoRocks(mock_url)

    return meteo_rocks_mock


@pytest.fixture
def mock_get():
    return response_generator()


@pytest.fixture
def mock_get_letter_wind_directions():
    return response_generator(mock_api_return(wind_dir="S"))


@pytest.fixture
def mock_get_invalid_wind_direction():
    invalid_wind_dir = 400
    return response_generator(mock_api_return(wind_dir=invalid_wind_dir))


@pytest.fixture
def mock_get_old_timestamp():
    old_timestamp = datetime.now() - timedelta(hours=OLD_TIMESTAMP_HOURS + 1)
    return response_generator(mock_api_return(timestamp=old_timestamp.timestamp()))


def test_meteo_rocks_instantiates_with_default_inherited_properties(
    mock_weather_station_info: MeteoRocks,
):
    # Arrange
    celsius_format = "C"
    wind_speed_format = "m/s"
    expected_string = "Temp: - | Wind: - - (Gust: -)"

    # Act & Assert
    assert mock_weather_station_info.url == td.valid_url
    assert mock_weather_station_info.temp_format == celsius_format
    assert mock_weather_station_info.wind_speed_format == wind_speed_format
    assert not mock_weather_station_info.temperature
    assert not mock_weather_station_info.wind_speed_avg
    assert not mock_weather_station_info.wind_speed_gust
    assert not mock_weather_station_info.wind_direction
    assert str(mock_weather_station_info) == expected_string


def test_meteo_rocks_get_data_sets_properties_correctly(
    mock_weather_station_info: MeteoRocks, mock_get: Response
):
    # Arrange
    mock_api_return_actual_timestamp = mock_api_return()

    expected_string = f"Temp: {mock_api_return_actual_timestamp['temp']:.1f} {mock_weather_station_info.temp_format} | Wind: {mock_api_return_actual_timestamp['windspeed_average']:.1f} {mock_weather_station_info.wind_speed_format} S (Gust: {mock_api_return_actual_timestamp['windspeed_gust']:.1f} {mock_weather_station_info.wind_speed_format})"
    with patch(
        "src.automatic_time_lapse_creator.weather_station_info.requests.get",
        return_value=mock_get,
    ):
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    assert (
        mock_weather_station_info.wind_speed_avg
        == mock_api_return_actual_timestamp["windspeed_average"]
    )
    assert (
        mock_weather_station_info.wind_speed_gust
        == mock_api_return_actual_timestamp["windspeed_gust"]
    )
    assert (
        mock_weather_station_info.wind_direction
        == mock_api_return_actual_timestamp["winddirection"]
    )
    assert (
        mock_weather_station_info.temperature
        == mock_api_return_actual_timestamp["temp"]
    )
    assert str(mock_weather_station_info) == expected_string


def test_meteo_rocks_get_data_returns_None_if_RequestException_is_raised(
    mock_weather_station_info: MeteoRocks,
):
    # Arrange
    response = Mock(spec=Response)

    with patch(
        "src.automatic_time_lapse_creator.weather_station_info.requests.get",
        return_value=response,
    ) as mock_response:
        response.status_code = 404
        response.raise_for_status.side_effect = RequestException
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    mock_response.json.assert_not_called()


def test_meteo_rocks_get_data_does_not_set_properties_if_ValueError_is_raised(
    mock_weather_station_info: MeteoRocks, mock_get: Response
):
    # Arrange
    expected_string = "Temp: - | Wind: - - (Gust: -)"
    with (
        patch(
            "src.automatic_time_lapse_creator.weather_station_info.requests.get",
            return_value=mock_get,
        ),
        patch(
            "src.automatic_time_lapse_creator.weather_station_info.datetime"
        ) as mock_datetime,
    ):
        mock_datetime.fromtimestamp.side_effect = ValueError
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    assert not mock_weather_station_info.temperature
    assert not mock_weather_station_info.wind_speed_avg
    assert not mock_weather_station_info.wind_speed_gust
    assert not mock_weather_station_info.wind_direction
    assert str(mock_weather_station_info) == expected_string


def test_meteo_rocks_get_data_does_not_set_properties_if_info_is_older_than_specified(
    mock_weather_station_info: MeteoRocks, mock_get_old_timestamp: Response
):
    # Arrange
    expected_string = "Temp: - | Wind: - - (Gust: -)"
    with patch(
        "src.automatic_time_lapse_creator.weather_station_info.requests.get",
        return_value=mock_get_old_timestamp,
    ):
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    assert not mock_weather_station_info.temperature
    assert not mock_weather_station_info.wind_speed_avg
    assert not mock_weather_station_info.wind_speed_gust
    assert not mock_weather_station_info.wind_direction
    assert str(mock_weather_station_info) == expected_string


def test_meteo_rocks_get_data_does_not_set_wind_direction_if_value_not_in_correct_range(
    mock_weather_station_info: MeteoRocks, mock_get_invalid_wind_direction: Response
):
    # Arrange
    with patch(
        "src.automatic_time_lapse_creator.weather_station_info.requests.get",
        return_value=mock_get_invalid_wind_direction,
    ):
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    assert mock_weather_station_info.temperature
    assert mock_weather_station_info.wind_speed_avg
    assert mock_weather_station_info.wind_speed_gust
    assert not mock_weather_station_info.wind_direction


def test_meteo_rocks_get_data_sets_properties_correctly_with_letter_wind_directions(
    mock_weather_station_info: MeteoRocks, mock_get_letter_wind_directions: Response
):
    # Arrange
    mock_api_return_actual_timestamp_letter_wind_direction = mock_api_return(
        wind_dir="S"
    )
    expected_string = f"Temp: {mock_api_return_actual_timestamp_letter_wind_direction['temp']:.1f} {mock_weather_station_info.temp_format} | Wind: {mock_api_return_actual_timestamp_letter_wind_direction['windspeed_average']:.1f} {mock_weather_station_info.wind_speed_format} S (Gust: {mock_api_return_actual_timestamp_letter_wind_direction['windspeed_gust']:.1f} {mock_weather_station_info.wind_speed_format})"
    with patch(
        "src.automatic_time_lapse_creator.weather_station_info.requests.get",
        return_value=mock_get_letter_wind_directions,
    ):
        # Act
        result = mock_weather_station_info.get_data()

    # Assert
    assert result is None
    assert (
        mock_weather_station_info.wind_speed_avg
        == mock_api_return_actual_timestamp_letter_wind_direction["windspeed_average"]
    )
    assert (
        mock_weather_station_info.wind_speed_gust
        == mock_api_return_actual_timestamp_letter_wind_direction["windspeed_gust"]
    )
    assert (
        mock_weather_station_info.wind_direction
        == mock_api_return_actual_timestamp_letter_wind_direction["winddirection"]
    )
    assert (
        mock_weather_station_info.temperature
        == mock_api_return_actual_timestamp_letter_wind_direction["temp"]
    )
    assert str(mock_weather_station_info) == expected_string


def test_WeatherStationInfo_get_wind_direction_returns_correct_values():
    # Arrange
    directions = list(range(0, 360, 22))
    expected = [
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
        "N",
    ]

    # Act
    for idx, direction in enumerate(directions):
        result = WeatherStationInfo._get_wind_direction(direction)  # type: ignore

        # Assert
        assert result == expected[idx]


def test_WeatherStationInfo_parse_float_parses_correctly():
    # Arrange
    valid_values: list[Any] = [12, "12", "12.5"]

    # Act
    for val in valid_values:
        result = WeatherStationInfo._parse_float(val)  # type: ignore

        # Assert
        assert isinstance(result, float)


def test_WeatherStationInfo_parse_float_returns_none_for_invalid_values():
    # Arrange
    valid_values: list[Any] = [None, "", "12,5", "string"]

    # Act
    for val in valid_values:
        result = WeatherStationInfo._parse_float(val)  # type: ignore

        # Assert
        assert result is None

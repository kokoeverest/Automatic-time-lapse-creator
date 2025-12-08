from src.automatic_time_lapse_creator.common.utils import (
    shorten,
    create_log_message,
    dash_sep_strings,
    create_description_for_monthly_video,
    DailyVideoResponse,
    MonthlyVideoResponse
)
from src.automatic_time_lapse_creator.common.constants import (
    DEFAULT_VIDEO_DESCRIPTION,
    MONTHLY_SUMMARY_VIDEO_DESCRIPTION,
    VideoType
)
from tests.test_data import sample_source_no_weather_data, sample_folder_path, sample_count
import os
from unittest.mock import patch
import json


def test_daily_video_response_returns_correct_json():
    # Arrange
    instance = DailyVideoResponse(
        video_path=sample_folder_path,
        images_count=sample_count,
        video_created=True,
        all_images_collected=True,
        images_partially_collected=False
    )

    # Act
    response_json = instance.to_json()
    expexted_result = json.loads(response_json)
    
    # Assert
    assert "video_files_count" not in expexted_result
    assert "images_count" in expexted_result
    assert "all_images_collected" in expexted_result
    assert "images_partially_collected" in expexted_result
    assert expexted_result["video_fps"] is None
    assert expexted_result["video_width"] is None
    assert expexted_result["video_height"] is None
    assert expexted_result["video_path"] is not None
    assert expexted_result["location_city_tz"] is None
    assert expexted_result["video_created"] is not None
    assert expexted_result["location_city_name"] is None
    assert expexted_result["source_location_name"] is None
    assert expexted_result["wait_before_next_frame"] is None
    assert expexted_result["video_type"] == VideoType.DAILY.value
    assert expexted_result["delete_collected_daily_images"] is None
    assert expexted_result["location_sunset_offset_minutes"] is None
    assert expexted_result["location_sunrise_offset_minutes"] is None
    assert expexted_result["nighttime_wait_before_next_retry"] is None
    assert expexted_result["delete_daily_videos_after_monthly_summary_is_created"] is None

def test_monthly_video_response_returns_correct_json():
    # Arrange
    instance = MonthlyVideoResponse(
        video_path=sample_folder_path,
        video_files_count=sample_count,
        video_created=True,
    )

    # Act
    response_json = instance.to_json()
    expexted_result = json.loads(response_json)
    
    # Assert
    assert "video_files_count" in expexted_result
    assert "images_count" not in expexted_result
    assert "all_images_collected" not in expexted_result
    assert "images_partially_collected" not in expexted_result
    assert expexted_result["video_fps"] is None
    assert expexted_result["video_width"] is None
    assert expexted_result["video_height"] is None
    assert expexted_result["video_path"] is not None
    assert expexted_result["location_city_tz"] is None
    assert expexted_result["video_created"] is not None
    assert expexted_result["location_city_name"] is None
    assert expexted_result["source_location_name"] is None
    assert expexted_result["wait_before_next_frame"] is None
    assert expexted_result["video_type"] == VideoType.MONTHLY.value
    assert expexted_result["delete_collected_daily_images"] is None
    assert expexted_result["location_sunset_offset_minutes"] is None
    assert expexted_result["location_sunrise_offset_minutes"] is None
    assert expexted_result["nighttime_wait_before_next_retry"] is None
    assert expexted_result["delete_daily_videos_after_monthly_summary_is_created"] is None

def test_create_description_for_monthly_video_returns_correct_string():
    # Arrange
    suffix = "January, 2020"
    expexcted_result = (
        f"{MONTHLY_SUMMARY_VIDEO_DESCRIPTION}{suffix}\n{DEFAULT_VIDEO_DESCRIPTION}"
    )

    # Act
    actual_result = create_description_for_monthly_video(sample_folder_path)

    # Assert
    assert expexcted_result == actual_result


def test_dash_sep_strings_returns_correctly_formatted_string():
    # Arrange
    year = "2020"
    expected_result = year

    # Act
    actual_result = dash_sep_strings(year)

    # Assert
    assert expected_result == actual_result


def test_dash_sep_strings_returns_empty_string_if_no_arguments_provided():
    # Arrange
    expected_result = ""

    # Act
    actual_result = dash_sep_strings()

    # Assert
    assert expected_result == actual_result


def test_dash_sep_strings_returns_correctly_formatted_string_if_more_arguments_are_provided():
    # Arrange
    year = "2020"
    month = "01"
    day = "15"
    expected_result = f"{year}-{month}-{day}"

    # Act
    actual_result = dash_sep_strings(year, month, day)

    # Assert
    assert expected_result == actual_result


def test_shorten_returns_correct_file_path():
    # Arrange
    file_path = os.path.join(
        "Automatic-time-lapse-creator",
        "stara_planina",
        "mazalat_hut",
        "2025-01-07",
        "2025-01-07.mp4",
    )
    expected = os.path.join(
        "stara_planina", "mazalat_hut", "2025-01-07", "2025-01-07.mp4"
    )

    # Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.common.utils.os.path.isdir",
        return_value=False,
    ):
        result = shorten(file_path)
        assert result == expected


def test_shorten_returns_correct_folder_path():
    # Arrange
    folder_path = os.path.join(
        "Automatic-time-lapse-creator", "stara_planina", "mazalat_hut", "2025-01-07"
    )
    expected = os.path.join("stara_planina", "mazalat_hut", "2025-01-07")

    # Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.common.utils.os.path.isdir", return_value=True
    ):
        result = shorten(folder_path)
        assert result == expected


def test_create_log_message_returns_correct_message_for_add_method():
    # Arrange
    expected = f"Source with location: {sample_source_no_weather_data.location_name} or url: {sample_source_no_weather_data.url} already exists!"

    #  Act
    result = create_log_message(sample_source_no_weather_data.location_name, sample_source_no_weather_data.url, "add")

    # Assert
    assert expected == result


def test_create_log_message_returns_correct_message_for_remove_method():
    # Arrange
    expected = f"Source with location: {sample_source_no_weather_data.location_name} or url: {sample_source_no_weather_data.url} doesn't exist!"

    #  Act
    result = create_log_message(
        sample_source_no_weather_data.location_name, sample_source_no_weather_data.url, "remove"
    )

    # Assert
    assert expected == result


def test_create_log_message_returns_correct_message_for_unknown_method():
    # Arrange
    unknown_method = "adddd"
    expected = f"Unknown command: {unknown_method}"

    #  Act
    result = create_log_message(
        sample_source_no_weather_data.location_name, sample_source_no_weather_data.url, unknown_method
    )

    # Assert
    assert expected == result

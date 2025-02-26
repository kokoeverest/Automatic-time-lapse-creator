import os
from unittest.mock import patch
from src.automatic_time_lapse_creator.source import ImageSource
from src.automatic_time_lapse_creator.common.constants import MP4_FILE, VideoPrivacyStatus

invalid_city_name = "Logator"
group_name = "Europe"
valid_source_name = "aleko"
valid_url = "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"
empty_url = "empty url"

with patch.object(ImageSource, "validate_url", return_value=True):
    sample_source_no_weather_data = ImageSource(valid_source_name, valid_url)
    duplicate_source = ImageSource(valid_source_name, valid_url)

    sample_source2_no_weather_data = ImageSource(
        "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
    )
    sample_source3_no_weather_data = ImageSource(
        "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
    )

with patch.object(ImageSource, "validate_url", return_value=False):
    non_existing_source = ImageSource(invalid_city_name, empty_url)
    sample_source_with_empty_url = ImageSource("fake", empty_url)

empty_dict = {}

sample_base_path = os.path.join("base", "path")
sample_folder_name_01 = "2020-01-01"
sample_folder_name_02 = "2020-01-02"

sample_year = "2020"
sample_month_january = "01"
sample_month_february = "02"

sample_video_file1 = os.path.join(sample_base_path, sample_folder_name_01, f"{sample_folder_name_01}{MP4_FILE}")
sample_video_file2 = os.path.join(sample_base_path, sample_folder_name_02, f"{sample_folder_name_02}{MP4_FILE}")

valid_json_content = '{"key": "value"}'
invalid_json_content = '{"key": "value"'

mock_secrets_file = "mock_secrets.json"
sample_folder_path = os.path.join("path", "to", sample_folder_name_01)

sample_date_time_text = "2025-01-01 12:00:00"
sample_weather_data_text = "Temp: 5.0C | Wind: 3.2m/s"

# video details
sample_video_title = "Sample Video Title"
sample_video_id = "video123"
sample_chunk_size = 5242880

# YouTube mocks
mock_channel_id = "UC1234567890"
mock_channel_response = {"items": [{"id": mock_channel_id}]}
mock_video_response = {
    "items": [
        {
            "snippet": {"title": sample_video_title},
            "id": {"videoId": sample_video_id},
        }
    ]
}
mock_empty_response: dict[str, list[str]] = {"items": []}
mock_mediaFileUpload_response = {"id": sample_video_id}

mock_video_list_response: dict[str, list[dict[str, str | dict[str, str]]]] = {
    "items": [
        {
            "id": sample_video_id,
            "snippet": {
                "title": sample_video_title
            },
            "status": {
                "uploadStatus": "uploaded",
                "privacyStatus": VideoPrivacyStatus.PUBLIC.value
            }
        }
    ]
}
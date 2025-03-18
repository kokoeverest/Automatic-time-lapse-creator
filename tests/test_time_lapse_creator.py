from queue import Queue
import pytest
from unittest.mock import MagicMock, mock_open, patch
import os
from logging import Logger

from src.automatic_time_lapse_creator.common.utils import dash_sep_strings
from src.automatic_time_lapse_creator.common.constants import (
    DEFAULT_DAY_FOR_MONTHLY_VIDEO,
    MP4_FILE,
    YYMMDD_FORMAT,
    DEFAULT_PATH_STRING,
    DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS,
    VIDEO_HEIGHT_360p,
    VIDEO_WIDTH_360p,
    DEFAULT_SUNSET_OFFSET,
    DEFAULT_SUNRISE_OFFSET,
    
)
from src.automatic_time_lapse_creator.source import Source
from src.automatic_time_lapse_creator.time_lapse_creator import (
    TimeLapseCreator,
)
from src.automatic_time_lapse_creator.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator.common.exceptions import (
    InvalidCollectionException,
)
import tests.test_data as td
from datetime import datetime as dt, timedelta
from astral import LocationInfo
import tests.test_mocks as tm


@pytest.fixture
def sample_empty_time_lapse_creator():
    return TimeLapseCreator()


@pytest.fixture
def sample_non_empty_time_lapse_creator():
    return TimeLapseCreator(
        [
            td.sample_source_no_weather_data,
            td.sample_source2_no_weather_data,
            td.sample_source3_no_weather_data,
        ],
        path=os.getcwd(),
        quiet_mode=False,
    )


fake_non_empty_time_lapse_creator = TimeLapseCreator(
    [td.sample_source_no_weather_data], path=os.getcwd()
)
fake_non_empty_time_lapse_creator.nighttime_wait_before_next_retry = 1


def test_initializes_correctly_with_default_config(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    assert isinstance(sample_empty_time_lapse_creator.folder_name, str)
    assert isinstance(sample_empty_time_lapse_creator.location, LocationAndTimeManager)
    assert isinstance(sample_empty_time_lapse_creator.sources, set)
    assert isinstance(sample_empty_time_lapse_creator.location.city, LocationInfo)
    assert isinstance(sample_empty_time_lapse_creator.logger, Logger)
    assert isinstance(sample_empty_time_lapse_creator.location.sunrise_offset, timedelta)
    assert isinstance(sample_empty_time_lapse_creator.location.sunset_offset, timedelta)
    assert sample_empty_time_lapse_creator.location.sunrise_offset.seconds == DEFAULT_SUNRISE_OFFSET * 60
    assert sample_empty_time_lapse_creator.location.sunset_offset.seconds == DEFAULT_SUNSET_OFFSET * 60
    assert sample_empty_time_lapse_creator.location.city.name == DEFAULT_CITY_NAME
    assert sample_empty_time_lapse_creator.folder_name == dt.today().strftime(
        YYMMDD_FORMAT
    )
    assert sample_empty_time_lapse_creator.base_path == os.path.join(
        os.getcwd(), DEFAULT_PATH_STRING
    )
    assert len(sample_empty_time_lapse_creator.sources) == 0
    assert (
        sample_empty_time_lapse_creator.wait_before_next_frame
        == DEFAULT_SECONDS_BETWEEN_FRAMES
    )
    assert (
        sample_empty_time_lapse_creator.nighttime_wait_before_next_retry
        == DEFAULT_NIGHTTIME_RETRY_SECONDS
    )
    assert sample_empty_time_lapse_creator.video_fps == DEFAULT_VIDEO_FPS
    assert sample_empty_time_lapse_creator.video_width == VIDEO_WIDTH_360p
    assert sample_empty_time_lapse_creator.video_height == VIDEO_HEIGHT_360p
    assert sample_empty_time_lapse_creator.quiet_mode
    assert sample_empty_time_lapse_creator.video_queue is None
    assert sample_empty_time_lapse_creator.log_queue is None
    assert sample_empty_time_lapse_creator.logger.name == "__root__"
    assert sample_empty_time_lapse_creator._monthly_summary # type: ignore
    assert sample_empty_time_lapse_creator._day_for_monthly_summary == DEFAULT_DAY_FOR_MONTHLY_VIDEO # type: ignore
    assert sample_empty_time_lapse_creator._delete_daily_videos # type: ignore

def test_validate_raises_TypeError_for_invalid_type(sample_empty_time_lapse_creator: TimeLapseCreator):
    # Arrange
    invalid_value = "invalid_type"

    # Act & Assert
    with pytest.raises(TypeError):
        sample_empty_time_lapse_creator._validate("sunrise_offset_minutes", invalid_value) # type: ignore


def test_validate_returns_value_within_range(sample_empty_time_lapse_creator: TimeLapseCreator):
    # Arrange
    valid_value = 150  # Within range for sunrise_offset_minutes

    # Act
    result = sample_empty_time_lapse_creator._validate("sunrise_offset_minutes", valid_value) # type: ignore

    # Assert
    assert result == valid_value


def test_validate_logs_warning_for_out_of_range_value(sample_empty_time_lapse_creator: TimeLapseCreator):
    # Arrange
    out_of_range_value = 500  # Out of range for sunrise_offset_minutes

    # Act & Assert
    with patch.object(sample_empty_time_lapse_creator.logger, "warning", return_value=None) as mock_warning:
        result = sample_empty_time_lapse_creator._validate("sunrise_offset_minutes", out_of_range_value) # type: ignore
        mock_warning.assert_called_once_with(
            f"sunrise_offset_minutes must be in range(1, 301)! Setting to default: {DEFAULT_SUNRISE_OFFSET}"
        )
        assert result == DEFAULT_SUNRISE_OFFSET


def test_validate_raises_KeyError_for_invalid_attr_name(sample_empty_time_lapse_creator: TimeLapseCreator):
    # Arrange
    invalid_attr_name = "invalid_attr"

    # Act & Assert
    with pytest.raises(KeyError):
        sample_empty_time_lapse_creator._validate(invalid_attr_name, 100) # type: ignore


def test_validate_handles_all_valid_attributes(sample_empty_time_lapse_creator: TimeLapseCreator):
    # Arrange
    valid_attributes = {
        "sunrise_offset_minutes": 100,
        "sunset_offset_minutes": 100,
        "seconds_between_frames": 300,
        "night_time_retry_seconds": 300,
        "video_fps": 30,
        "video_width": 1280,
        "video_height": 720,
    }

    # Act & Assert
    for attr_name, attr_value in valid_attributes.items():
        result = sample_empty_time_lapse_creator._validate(attr_name, attr_value) # type: ignore
        assert result == attr_value

def test_sources_not_empty_returns_false_with_no_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with pytest.raises(ValueError):
        result = sample_empty_time_lapse_creator.verify_sources_not_empty()
        assert result == "You should add at least one source for this location!"


def test_sources_not_empty_returns_true_when_source_is_added(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    assert not sample_non_empty_time_lapse_creator.verify_sources_not_empty()


def test_validate_collection_raises_InvalidCollectionEception_if_a_dict_is_passed():
    # Arrange, Act & Assert
    with pytest.raises(InvalidCollectionException):
        result = TimeLapseCreator.validate_collection(td.empty_dict)  # type: ignore
        assert result == "Only list, tuple or set collections are allowed!"


def test_validate_collection_returns_set_with_sources_if_valid_collections_are_passed():
    # Arrange
    allowed_collections = (set, list, tuple)

    # Act & Assert
    for col in allowed_collections:
        argument = col([td.sample_source_no_weather_data, td.sample_source2_no_weather_data])  # type: ignore

        result = TimeLapseCreator.validate_collection(argument)  # type: ignore
        assert isinstance(result, set)


def test_check_sources_raises_InvalidCollectionEception_if_a_dict_is_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with pytest.raises(InvalidCollectionException):
        result = sample_empty_time_lapse_creator.check_sources(td.empty_dict)  # type: ignore
        assert result == "Only list, tuple or set collections are allowed!"


def test_check_sources_returns_Source_if_a_single_valid_source_is_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    result = sample_empty_time_lapse_creator.check_sources(
        td.sample_source_no_weather_data
    )

    # Assert
    assert isinstance(result, Source)


def test_check_sources_returns_set_with_sources_if_valid_collections_are_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    allowed_collections = (set, list, tuple)

    # Act & Assert
    for col in allowed_collections:
        argument = col([td.sample_source_no_weather_data, td.sample_source2_no_weather_data])  # type: ignore

        result = sample_empty_time_lapse_creator.check_sources(argument)  # type: ignore
        assert isinstance(result, set)


def test_add_sources_successfully_adds_one_source(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    sample_empty_time_lapse_creator.add_sources({td.sample_source_no_weather_data})

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 1


def test_add_sources_successfully_adds_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    result = sample_empty_time_lapse_creator.add_sources(
        {
            td.sample_source_no_weather_data,
            td.sample_source2_no_weather_data,
            td.sample_source3_no_weather_data,
        }
    )

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3
    assert not result


def test_add_sources_doesnt_add_source_if_duplicate_name_or_url_is_found(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_empty_time_lapse_creator.add_sources({td.sample_source_no_weather_data})

    # Act & Assert
    with (
        patch.object(
            sample_empty_time_lapse_creator.logger, "warning", return_value=None
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
    ):
        sample_empty_time_lapse_creator.add_sources({td.duplicate_source})
        assert mock_logger.call_count == 1
        assert mock_util.call_count == 1
        assert len(sample_empty_time_lapse_creator.sources) == 1


def test_add_sources_doesnt_add_source_if_duplicate_name_or_url_is_found_in_a_collection(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    with (
        patch.object(
            sample_empty_time_lapse_creator.logger, "warning", return_value=None
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
    ):
        result = sample_empty_time_lapse_creator.add_sources(
            {
                td.sample_source_no_weather_data,
                td.sample_source2_no_weather_data,
                td.sample_source3_no_weather_data,
                td.duplicate_source,
            }
        )

    # Assert
    assert mock_logger.call_count == 1
    assert mock_util.call_count == 1
    assert len(sample_empty_time_lapse_creator.sources) == 3
    assert not result


def test_remove_sources_successfully_removes_a_single_source(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    sample_empty_time_lapse_creator.add_sources(
        {
            td.sample_source_no_weather_data,
            td.sample_source2_no_weather_data,
            td.sample_source3_no_weather_data,
        }
    )

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3

    sample_empty_time_lapse_creator.remove_sources(td.sample_source_no_weather_data)
    assert len(sample_empty_time_lapse_creator.sources) == 2


def test_remove_sources_successfully_removes_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_empty_time_lapse_creator.add_sources(
        {
            td.sample_source_no_weather_data,
            td.sample_source2_no_weather_data,
            td.sample_source3_no_weather_data,
        }
    )

    # Act & Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3

    result = sample_empty_time_lapse_creator.remove_sources(
        {td.sample_source_no_weather_data, td.sample_source2_no_weather_data}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 1
    assert not result


def test_remove_sources_doesnt_remove_a_source_if_source_is_not_found(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    with (
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "warning", return_value=None
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
        patch.object(Source, "validate_url", return_value=True),
    ):
        result = sample_non_empty_time_lapse_creator.remove_sources(
            td.non_existing_source
        )

    # Assert
    assert mock_logger.call_count == 1
    assert mock_util.call_count == 1
    assert len(sample_non_empty_time_lapse_creator.sources) == 3
    assert not result


def test_remove_sources_doesnt_remove_a_source_if_source_is_not_found_in_a_collection(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    with (
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "warning", return_value=None
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
        patch.object(Source, "validate_url", return_value=True),
    ):
        result = sample_non_empty_time_lapse_creator.remove_sources(
            [td.sample_source_no_weather_data, td.non_existing_source]
        )

    # Assert
    assert mock_logger.call_count == 1
    assert mock_util.call_count == 1
    assert len(sample_non_empty_time_lapse_creator.sources) == 2
    assert not result


def test_reset_images_partially_collected(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    for source in sample_non_empty_time_lapse_creator.sources:
        source.set_images_partially_collected()

    # Act
    sample_non_empty_time_lapse_creator.reset_images_partially_collected()

    # Assert
    for source in sample_non_empty_time_lapse_creator.sources:
        assert not source.images_partially_collected


def test_set_sources_all_images_collected_sets_images_collected_to_True_for_all_sources(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    sample_non_empty_time_lapse_creator.set_sources_all_images_collected()

    # Assert
    for source in sample_non_empty_time_lapse_creator.sources:
        assert source.images_collected
        assert not source.images_partially_collected


def test_reset_all_sources_counters_to_default_values(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_non_empty_time_lapse_creator.set_sources_all_images_collected()
    for source in sample_non_empty_time_lapse_creator.sources:
        source.set_daily_video_created()
        source.increase_images()

    # Act
    sample_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()

    # Assert
    for source in sample_non_empty_time_lapse_creator.sources:
        assert not source.daily_video_created
        assert source.images_count == 0
        assert not source.images_collected
        assert not source.images_partially_collected


def test_create_video_returns_False_if_video_is_not_created(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
            return_value=False,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
            return_value=False,
        ),
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert not sample_non_empty_time_lapse_creator.create_video(source)
            assert not source.daily_video_created


def test_create_video_returns_True_if_video_is_created(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
            return_value=False,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.create_timelapse",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_media_files",
            return_value=True,
        ) as mock_delete,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger_info,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert len(sample_non_empty_time_lapse_creator.sources) == 3
            assert sample_non_empty_time_lapse_creator.create_video(source)
            assert not source.daily_video_created

        assert mock_delete.call_count == 3
        assert mock_logger_info.call_count == 3


def test_create_video_returns_True_if_video_is_created_and_source_images_are_not_deleted(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
            return_value=False,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.create_timelapse",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_media_files",
            return_value=True,
        ) as mock_delete,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger_info,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert len(sample_non_empty_time_lapse_creator.sources) == 3
            assert sample_non_empty_time_lapse_creator.create_video(
                source, delete_source_images=False
            )
            assert not source.daily_video_created

        assert mock_logger_info.call_count == 3
        assert mock_delete.call_count == 0


def test_create_video_returns_True_if_video_exists(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_media_files",
            return_value=True,
        ) as mock_delete,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger_info,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert len(sample_non_empty_time_lapse_creator.sources) == 3
            assert sample_non_empty_time_lapse_creator.create_video(source)
            assert not source.daily_video_created

        assert mock_delete.call_count == 3
        assert mock_logger_info.call_count == 0


def test_collect_images_from_webcams_returns_False_if_not_daylight(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    monkeypatch.setattr(
        sample_non_empty_time_lapse_creator.location, "is_daylight", lambda: False
    )

    # Act & Assert
    with patch.object(
        sample_non_empty_time_lapse_creator.logger, "info", return_value=None
    ) as mock_logger:
        assert not sample_non_empty_time_lapse_creator.collect_images_from_webcams()
        assert mock_logger.call_count == 1


def test_collect_images_from_webcams_returns_True_if_daylight_and_all_images_collected(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    mock_file = mock_open()
    bools = [True, True]

    def mock_bool():
        if len(bools) > 0:
            return bools.pop(0)
        else:
            return False

    with (
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.Path.mkdir",
            return_value=None,
        ),
        patch("builtins.open", mock_file),
        patch(
            "src.automatic_time_lapse_creator.source.Source.get_frame_bytes",
            return_value=b"some_content",
        ),
    ):
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator.location, "is_daylight", mock_bool
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "cache_self", tm.mock_None
        )
        sample_non_empty_time_lapse_creator.wait_before_next_frame = 0

        # Act & Assert
        assert sample_non_empty_time_lapse_creator.collect_images_from_webcams()
        assert mock_logger.call_count == 2


def test_collect_images_from_webcams_returns_True_even_if_request_returns_Exception(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    mock_file = mock_open()
    bools = [True, True]

    def mock_bool():
        if len(bools) > 0:
            return bools.pop(0)
        else:
            return False

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.Path.mkdir",
            return_value=None,
        ),
        patch(
            "src.automatic_time_lapse_creator.source.Source.get_frame_bytes",
            return_value=Exception,
        ),
        patch("builtins.open", mock_file),
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger_info,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "error", return_value=None
        ) as mock_logger_error,
    ):
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator.location, "is_daylight", mock_bool
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "cache_self", lambda: None
        )
        sample_non_empty_time_lapse_creator.wait_before_next_frame = 0

        # Act & Assert
        assert sample_non_empty_time_lapse_creator.collect_images_from_webcams()
        assert mock_logger_info.call_count == 2
        assert mock_logger_error.call_count == 0


def test_execute_sleeps_if_images_are_not_collected(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    monkeypatch.setattr(
        sample_non_empty_time_lapse_creator, "verify_sources_not_empty", lambda: True
    )
    monkeypatch.setattr(
        sample_non_empty_time_lapse_creator,
        "collect_images_from_webcams",
        lambda: False,
    )

    # Act
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.sleep",
            return_value=None,
        ) as mock_sleep,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger_info,
        patch.object(
            sample_non_empty_time_lapse_creator, "is_next_month", return_value=False
        ),
        patch(
            "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
            return_value=sample_non_empty_time_lapse_creator,
        ),
    ):
        sample_non_empty_time_lapse_creator.nighttime_wait_before_next_retry = 1
        sample_non_empty_time_lapse_creator.execute()

        # Assert
        assert mock_logger_info.call_count == 1
        mock_sleep.assert_called_once_with(
            sample_non_empty_time_lapse_creator.nighttime_wait_before_next_retry
        )


def test_execute_creates_video_for_every_source_when_all_images_are_collected():
    # Arrange, Act & Assert
    with (
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.logger.info",
            return_value=None,
        ) as mock_logger_info,
        patch(
            "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
            return_value=fake_non_empty_time_lapse_creator,
        ),
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.verify_sources_not_empty",
            return_value=True,
        ),
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.collect_images_from_webcams",
            return_value=True,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_manager.dt"
        ) as mock_datetime,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.create_video",
            return_value=True,
        ) as mock_create_video,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.cache_self",
            return_value=None,
        ) as mock_cache,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.sleep",
            return_value=None,
        ) as mock_sleep,
    ):
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        fake_non_empty_time_lapse_creator.set_sources_all_images_collected()

        fake_non_empty_time_lapse_creator.execute()
        assert mock_logger_info.call_count == 1
        assert mock_cache.call_count == 1
        assert mock_sleep.call_count == 0
        assert mock_create_video.call_count == len(
            fake_non_empty_time_lapse_creator.sources
        )
        for source in fake_non_empty_time_lapse_creator.sources:
            mock_create_video.assert_called_once_with(source)
            assert source.daily_video_created

        # Tear down
        fake_non_empty_time_lapse_creator.reset_test_counter()


def test_execute_creates_video_for_every_source_when_images_partially_collected():
    # Arrange, Act & Assert
    with (
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.logger.info",
            return_value=None,
        ) as mock_logger_info,
        patch(
            "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
            return_value=fake_non_empty_time_lapse_creator,
        ),
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.verify_sources_not_empty",
            return_value=True,
        ),
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.collect_images_from_webcams",
            return_value=True,
        ) as mock_collect,
        patch(
            "src.automatic_time_lapse_creator.time_manager.dt"
        ) as mock_datetime,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.create_video",
            return_value=True,
        ) as mock_create_video,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.sleep",
            return_value=None,
        ) as mock_sleep,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.cache_self",
            return_value=None,
        ) as mock_cache,
    ):
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        fake_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()

        for source in fake_non_empty_time_lapse_creator.sources:
            source.set_images_partially_collected()

        fake_non_empty_time_lapse_creator.execute()
        assert mock_logger_info.call_count == 1
        assert mock_cache.call_count == 1
        assert mock_collect.called
        assert mock_sleep.call_count == 0
        assert mock_create_video.call_count == len(
            fake_non_empty_time_lapse_creator.sources
        )
        for source in fake_non_empty_time_lapse_creator.sources:
            mock_create_video.assert_called_once_with(
                source, delete_source_images=False
            )
            assert source.daily_video_created

        # Tear down
        fake_non_empty_time_lapse_creator.reset_test_counter()


def test_get_cached_self_returns_old_object_if_retrieved_at_the_same_day():
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
        return_value=fake_non_empty_time_lapse_creator,
    ):
        result = fake_non_empty_time_lapse_creator.get_cached_self()
        assert result == fake_non_empty_time_lapse_creator
        assert result.folder_name == fake_non_empty_time_lapse_creator.folder_name

    # Tear down
    fake_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()


def test_get_cached_self_returns_old_object_if_retrieved_at_the_same_day_and_images_were_partially_collected():
    # Arrange
    sample_cached_creator = TimeLapseCreator([td.sample_source_no_weather_data])
    [
        source.set_images_partially_collected()
        for source in sample_cached_creator.sources
    ]

    #  Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
        return_value=sample_cached_creator,
    ):
        result = fake_non_empty_time_lapse_creator.get_cached_self()
        assert result != fake_non_empty_time_lapse_creator
        assert result.folder_name == fake_non_empty_time_lapse_creator.folder_name
        for idx, source in enumerate(result.sources):
            assert source.images_partially_collected
            assert list(fake_non_empty_time_lapse_creator.sources)[
                idx
            ].images_partially_collected

    # Tear down
    fake_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()


def test_get_cached_self_returns_self_if_cache_rerurns_exception():
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
        return_value=Exception(),
    ):
        result = fake_non_empty_time_lapse_creator.get_cached_self()
        assert result == fake_non_empty_time_lapse_creator
        assert result.folder_name == fake_non_empty_time_lapse_creator.folder_name

    # Tear down
    fake_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()


def test_cache_self_returns_None():
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.cache_manager.CacheManager.write",
        return_value=None,
    ):
        assert fake_non_empty_time_lapse_creator.cache_self() is None


def test_clear_cache_returns_None():
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.cache_manager.CacheManager.clear_cache",
        return_value=None,
    ):
        assert fake_non_empty_time_lapse_creator.clear_cache() is None


def test_is_it_next_day_changes_folder_name_and_creates_new_LocationAndTimeManger(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    old_date = tm.MockDatetime.fake_today
    old_folder_name = sample_non_empty_time_lapse_creator.folder_name
    old_location = sample_non_empty_time_lapse_creator.location

    # Act & Assert
    for fake_date in [
        tm.MockDatetime.fake_next_year,
        tm.MockDatetime.fake_next_month,
        tm.MockDatetime.fake_next_day,
    ]:
        with (
            patch(
                "src.automatic_time_lapse_creator.time_lapse_creator.dt"
            ) as mock_today,
            patch.object(
                sample_non_empty_time_lapse_creator.logger, "info", return_value=None
            ) as mock_logger_info,
        ):
            mock_today.strptime.return_value = tm.MockDatetime.fake_today
            mock_today.today.return_value = fake_date
            sample_non_empty_time_lapse_creator.is_it_next_day()

            assert old_date < fake_date
            assert (
                old_folder_name is not sample_non_empty_time_lapse_creator.folder_name
            )
            assert old_location is sample_non_empty_time_lapse_creator.location
            assert mock_logger_info.call_count == 1


def test_is_it_next_day_does_not_change_anything_if_it_is_the_same_day(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    old_date = tm.MockDatetime.fake_today
    old_folder_name = sample_non_empty_time_lapse_creator.folder_name
    old_location = sample_non_empty_time_lapse_creator.location

    # Act & Assert

    with (patch("src.automatic_time_lapse_creator.time_lapse_creator.dt") as mock_today,
          patch("src.automatic_time_lapse_creator.time_manager.dt") as mock_now):
        mock_today.strptime.return_value = tm.MockDatetime.fake_today
        mock_now.now.return_value = tm.MockDatetime.fake_today
        sample_non_empty_time_lapse_creator.is_it_next_day()

        assert old_date == tm.MockDatetime.fake_today
        assert old_folder_name is sample_non_empty_time_lapse_creator.folder_name
        assert old_location is sample_non_empty_time_lapse_creator.location


def test_valid_folder_returns_True_with_valid_folder_name():
    # Arrange
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.isdir",
            return_value=True,
        ) as mock_isdir,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.join",
            return_value=f"{td.sample_base_path}/{td.sample_folder_name_01}",
        ) as mock_join,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dash_sep_strings",
            return_value=f"{td.sample_year}-{td.sample_month_january}",
        ) as mock_dash_sep,
    ):
        # Act
        result = TimeLapseCreator.valid_folder(
            td.sample_base_path,
            td.sample_folder_name_01,
            td.sample_year,
            td.sample_month_january,
        )

        # Assert
        mock_isdir.assert_called_once_with(
            f"{td.sample_base_path}/{td.sample_folder_name_01}"
        )
        mock_join.assert_called_once_with(td.sample_base_path, td.sample_folder_name_01)
        mock_dash_sep.assert_called_once_with(td.sample_year, td.sample_month_january)
        assert result


def test_valid_folder_returns_False_when_folder_does_not_exist():
    # Arrange
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.isdir",
            return_value=False,
        ) as mock_isdir,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.join",
            return_value=f"{td.sample_base_path}/{td.sample_folder_name_01}",
        ) as mock_join,
    ):
        # Act
        result = TimeLapseCreator.valid_folder(
            td.sample_base_path,
            td.sample_folder_name_01,
            td.sample_year,
            td.sample_month_january,
        )

        # Assert
        mock_isdir.assert_called_once_with(
            f"{td.sample_base_path}/{td.sample_folder_name_01}"
        )
        mock_join.assert_called_once_with(td.sample_base_path, td.sample_folder_name_01)
        assert not result


def test_valid_folder_returns_False_when_folder_name_does_not_match():
    # Arrange
    invalid_folder_path = "2025-04"

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.isdir",
            return_value=True,
        ) as mock_isdir,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.join",
            return_value=f"{td.sample_base_path}/{td.sample_folder_name_01}",
        ) as mock_join,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dash_sep_strings",
            return_value=invalid_folder_path,
        ) as mock_dash_sep,
    ):
        # Act
        result = TimeLapseCreator.valid_folder(
            td.sample_base_path,
            td.sample_folder_name_01,
            td.sample_year,
            td.sample_month_january,
        )

        # Assert
        mock_isdir.assert_called_once_with(
            f"{td.sample_base_path}/{td.sample_folder_name_01}"
        )
        mock_join.assert_called_once_with(td.sample_base_path, td.sample_folder_name_01)
        mock_dash_sep.assert_called_once_with(td.sample_year, td.sample_month_january)
        assert not result


def test_get_video_files_paths_returns_correct_paths(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    folders = [td.sample_folder_name_01, td.sample_folder_name_02]
    expected_paths = [td.sample_video_file1, td.sample_video_file2]

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.listdir",
            return_value=folders,
        ) as mock_listdir,
        patch.object(
            sample_non_empty_time_lapse_creator,
            "valid_folder",
            return_value=True,
        ) as mock_valid_folder,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.glob",
            side_effect=lambda path: [td.sample_video_file1] # type: ignore
            if td.sample_folder_name_01 in path
            else [td.sample_video_file2],
        ) as mock_glob,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.get_video_files_paths(
            td.sample_base_path, td.sample_year, td.sample_month_january
        )

        # Assert
        mock_listdir.assert_called_once_with(td.sample_base_path)
        assert mock_valid_folder.call_count == 2
        assert mock_glob.call_count == 2
        assert result == expected_paths


def test_get_video_files_paths_skips_invalid_folders(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    folders = [td.sample_folder_name_01, "invalid_folder"]
    expected_paths = [td.sample_video_file1]

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.listdir",
            return_value=folders,
        ) as mock_listdir,
        patch.object(
            sample_non_empty_time_lapse_creator,
            "valid_folder",
            side_effect=lambda base, folder, y, m: folder == td.sample_folder_name_01, # type: ignore
        ) as mock_valid_folder,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.glob",
            return_value=[td.sample_video_file1],
        ) as mock_glob,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.get_video_files_paths(
            td.sample_base_path, td.sample_year, td.sample_month_january
        )

        # Assert
        mock_listdir.assert_called_once_with(td.sample_base_path)
        assert mock_valid_folder.call_count == 2
        assert mock_glob.call_count == 1
        assert result == expected_paths


def test_get_video_files_paths_returns_empty_if_no_valid_folders(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    folders = ["invalid_folder1", "invalid_folder2"]
    expected_paths = []

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.listdir",
            return_value=folders,
        ) as mock_listdir,
        patch.object(
            sample_non_empty_time_lapse_creator, "valid_folder", return_value=False
        ) as mock_valid_folder,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.glob", return_value=[]
        ) as mock_glob,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.get_video_files_paths(
            td.sample_base_path, td.sample_year, td.sample_month_january
        )

        # Assert
        mock_listdir.assert_called_once_with(td.sample_base_path)
        assert mock_valid_folder.call_count == 2
        assert mock_glob.call_count == 0
        assert result == expected_paths


def test_get_video_files_paths_ignores_empty_video_files(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    folders = [td.sample_folder_name_01]
    video_files = [""]
    expected_paths = []

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.listdir",
            return_value=folders,
        ) as mock_listdir,
        patch.object(
            sample_non_empty_time_lapse_creator, "valid_folder", return_value=True
        ) as mock_valid_folder,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.glob",
            return_value=video_files,
        ) as mock_glob,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.get_video_files_paths(
            td.sample_base_path, td.sample_year, td.sample_month_january
        )

        # Assert
        mock_listdir.assert_called_once_with(td.sample_base_path)
        assert mock_valid_folder.call_count == 1
        assert mock_glob.call_count == 1
        assert result == expected_paths


def test_create_monthly_video_creates_video_and_keeps_existing_daily_videos(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    yy_mm_format = dash_sep_strings(td.sample_year, td.sample_month_january)
    video_files = [td.sample_video_file1, td.sample_video_file2]
    video_folder_name = os.path.join(td.sample_base_path, yy_mm_format)
    output_video_name = os.path.join(video_folder_name, f"{yy_mm_format}{MP4_FILE}")

    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_video_files_paths",
            return_value=video_files,
        ) as mock_get_video_files_paths,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.create_monthly_summary_video",
            return_value=True,
        ) as mock_create_monthly_summary_video,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_media_files",
            return_value=True,
        ) as mock_delete_media_files,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.join",
            side_effect=os.path.join,
        ) as mock_path_join,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.split",
            return_value= ("", ""),
        ) as mock_path_split,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.shorten",
            return_value="",
        ) as mock_shorten,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info", return_value=None
        ) as mock_logger,
    ):
        
        sample_non_empty_time_lapse_creator._delete_daily_videos = False # type: ignore
        # Act
        result = sample_non_empty_time_lapse_creator.create_monthly_video(
            base_path=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_january,
        )

        # Assert
        mock_get_video_files_paths.assert_called_once_with(
            base_folder=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_january,
        )
        mock_create_monthly_summary_video.assert_called_once_with(
            logger=sample_non_empty_time_lapse_creator.logger,
            video_paths=video_files,
            output_video_path=output_video_name,
            fps=DEFAULT_VIDEO_FPS,
        )
        mock_shorten.assert_called_once_with(output_video_name)
        assert mock_delete_media_files.call_count == 0
        assert mock_path_split.call_count == 0
        assert mock_path_join.call_count == 2
        assert result == video_folder_name
        assert mock_logger.call_count == 1


def test_create_monthly_video_no_video_files(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    yy_mm_format = dash_sep_strings(td.sample_year, td.sample_month_february)
    output_video_name = os.path.join(
        td.sample_base_path, yy_mm_format, f"{yy_mm_format}{MP4_FILE}"
    )

    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_video_files_paths",
            return_value=[],
        ) as mock_get_video_files_paths,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.os.path.join",
            side_effect=os.path.join,
        ),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.shorten",
            return_value="",
        ) as mock_shorten,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "warning"
        ) as mock_logger_warning,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.create_monthly_video(
            base_path=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_february,
        )

        # Assert
        mock_get_video_files_paths.assert_called_once_with(
            base_folder=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_february,
        )
        mock_logger_warning.assert_called_once_with(
            f"No folders found for a monthly summary video - {''}!"
        )
        mock_shorten.assert_called_once_with(output_video_name)
        assert mock_shorten.call_count == 1
        assert result is None


def test_create_monthly_video_deletes_source_files(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    yy_mm_format = dash_sep_strings(td.sample_year, td.sample_month_january)
    video_files = [td.sample_video_file1, td.sample_video_file2]
    video_folder_name = os.path.join(td.sample_base_path, yy_mm_format)
    output_video_name = os.path.join(video_folder_name, f"{yy_mm_format}{MP4_FILE}")

    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_video_files_paths",
            return_value=video_files,
        ) as mock_get_video_files_paths,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.create_monthly_summary_video",
            return_value=True,
        ) as mock_create_monthly_summary_video,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_media_files"
        ) as mock_delete_source_media_files,
    ):
        # Act
        result = sample_non_empty_time_lapse_creator.create_monthly_video(
            base_path=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_january,
        )

        # Assert
        mock_get_video_files_paths.assert_called_once_with(
            base_folder=td.sample_base_path,
            year=td.sample_year,
            month=td.sample_month_january,
        )
        mock_create_monthly_summary_video.assert_called_once_with(
            logger=sample_non_empty_time_lapse_creator.logger,
            video_paths=video_files,
            output_video_path=output_video_name,
            fps=DEFAULT_VIDEO_FPS,
        )
        assert mock_delete_source_media_files.call_count == len(video_files)
        for video_path in video_files:
            head, _ = os.path.split(video_path)
            mock_delete_source_media_files.assert_any_call(
                logger=sample_non_empty_time_lapse_creator.logger,
                path=head,
                extension=MP4_FILE,
                delete_folder=True,
            )
        assert result == video_folder_name


def test_is_next_month_true(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dt",
        ) as mock_dt,
    ):
        mock_dt.today.return_value = tm.MockDatetime.fake_day_for_a_monthly_video
        mock_dt.now.return_value = tm.MockDatetime.fake_now
        # Act
        result = sample_non_empty_time_lapse_creator.is_next_month()

        # Assert
        assert result is True


def test_is_next_month_false_wrong_day(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dt",
        ) as mock_dt,
    ):
        mock_dt.today.return_value = tm.MockDatetime.fake_today
        mock_dt.now.return_value = tm.MockDatetime.fake_now
        # Act
        result = sample_non_empty_time_lapse_creator.is_next_month()

        # Assert
        assert result is False


def test_is_next_month_false_wrong_hour(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dt",
        ) as mock_dt,
    ):
        mock_dt.today.return_value = tm.MockDatetime.fake_day_for_a_monthly_video
        mock_dt.now.return_value = tm.MockDatetime.fake_now_wrong_hour

        # Act
        result = sample_non_empty_time_lapse_creator.is_next_month()

        # Assert
        assert result is False


def test_is_next_month_logs_info(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_non_empty_time_lapse_creator.quiet_mode = False

    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.dt",
        ) as mock_dt,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info"
        ) as mock_logger_info,
    ):
        mock_dt.today.return_value = tm.MockDatetime.fake_day_for_a_monthly_video
        mock_dt.now.return_value = tm.MockDatetime.fake_now_wrong_hour
        # Act
        result = sample_non_empty_time_lapse_creator.is_next_month()

        # Assert
        assert result is False
        mock_logger_info.assert_called_once_with("Not next month")


def test_process_monthly_summary_not_executed_when_videos_are_created(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_previous_year_and_month",
            return_value=(td.sample_year, td.sample_month_january),
        ) as mock_get_year_month,
        patch.object(
            sample_non_empty_time_lapse_creator,
            "create_monthly_video",
        ) as mock_create_video,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info"
        ) as mock_logger_info,
    ):
        [
            src.set_monthly_video_created()
            for src in sample_non_empty_time_lapse_creator.sources
        ]
        # Act
        sample_non_empty_time_lapse_creator.process_monthly_summary()

        # Assert
        mock_get_year_month.assert_called_once()
        assert mock_create_video.call_count == 0
        assert mock_logger_info.call_count == 0

        # Tear down
        [
            src.reset_monthly_video_created()
            for src in sample_non_empty_time_lapse_creator.sources
        ]


def test_process_monthly_summary_creates_videos_and_sends_to_queue(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    mock_video_queue = MagicMock(spec=Queue)
    sample_non_empty_time_lapse_creator.video_queue = mock_video_queue

    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_previous_year_and_month",
            return_value=(td.sample_year, td.sample_month_january),
        ) as mock_get_year_month,
        patch.object(
            sample_non_empty_time_lapse_creator,
            "create_monthly_video",
            return_value=td.sample_video_file1,
        ) as mock_create_video,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info"
        ) as mock_logger_info,
    ):
        # Act
        sample_non_empty_time_lapse_creator.process_monthly_summary()

        # Assert
        mock_get_year_month.assert_called_once()
        assert mock_create_video.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )
        assert mock_video_queue.put.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )
        assert mock_logger_info.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )
    for src in sample_non_empty_time_lapse_creator.sources:
        mock_create_video.assert_any_call(
            os.path.join(
                sample_non_empty_time_lapse_creator.base_path, src.location_name
            ),
            td.sample_year,
            td.sample_month_january,
        )
        assert src.monthly_video_created
    
    # Tear down
    [
        src.reset_monthly_video_created()
        for src in sample_non_empty_time_lapse_creator.sources
    ]


def test_process_monthly_summary_no_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with patch.object(
        sample_empty_time_lapse_creator.logger, "info"
    ) as mock_logger_info:
        # Act
        sample_empty_time_lapse_creator.process_monthly_summary()

        # Assert
        mock_logger_info.assert_not_called()


def test_process_monthly_summary_no_video_queue(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    with (
        patch.object(
            sample_non_empty_time_lapse_creator,
            "get_previous_year_and_month",
            return_value=(td.sample_year, td.sample_month_january),
        ) as mock_get_year_month,
        patch.object(
            sample_non_empty_time_lapse_creator,
            "create_monthly_video",
            return_value=td.sample_video_file1,
        ) as mock_create_video,
        patch.object(
            sample_non_empty_time_lapse_creator.logger, "info"
        ) as mock_logger_info,
    ):
        # Act
        sample_non_empty_time_lapse_creator.process_monthly_summary()

        # Assert
        mock_get_year_month.assert_called_once()
        for src in sample_non_empty_time_lapse_creator.sources:
            assert src.monthly_video_created
            mock_create_video.assert_any_call(
                os.path.join(
                    sample_non_empty_time_lapse_creator.base_path, src.location_name
                ),
                td.sample_year,
                td.sample_month_january,
            )
        assert mock_logger_info.call_count == len(
            sample_non_empty_time_lapse_creator.sources
        )

        # Tear down
        [
            src.reset_monthly_video_created()
            for src in sample_non_empty_time_lapse_creator.sources
        ]


def test_get_previous_year_and_month_returns_tuple_with_correct_values(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    """
    Testing the function with a change of the month and change of the year"""
    # Arrange
    inputs = [
        f"2020-02-{DEFAULT_DAY_FOR_MONTHLY_VIDEO}",
        f"2020-01-{DEFAULT_DAY_FOR_MONTHLY_VIDEO}",
    ]

    expected = [("2020", "01"), ("2019", "12")]

    # Act & Assert
    for idx, inp in enumerate(inputs):
        sample_empty_time_lapse_creator.folder_name = inp
        result = sample_empty_time_lapse_creator.get_previous_year_and_month()
        assert result == expected[idx]

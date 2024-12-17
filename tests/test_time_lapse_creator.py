import pytest
from unittest.mock import mock_open, patch
import os

import requests
from src.automatic_time_lapse_creator.common.constants import (
    YYMMDD_FORMAT,
    DEFAULT_PATH_STRING,
    DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_VIDEO_WIDTH,
)
from src.automatic_time_lapse_creator.source import Source
from src.automatic_time_lapse_creator.time_lapse_creator import (
    TimeLapseCreator,
)
from src.automatic_time_lapse_creator.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator.common.exceptions import (
    InvalidStatusCodeException,
    InvalidCollectionException,
)
import tests.test_data as td
from datetime import datetime as dt
from astral import LocationInfo
import tests.test_mocks as tm


@pytest.fixture
def sample_empty_time_lapse_creator():
    return TimeLapseCreator()


@pytest.fixture
def sample_non_empty_time_lapse_creator():
    return TimeLapseCreator(
        [td.sample_source1, td.sample_source2, td.sample_source3], path=os.getcwd()
    )


fake_non_empty_time_lapse_creator = TimeLapseCreator(
    [td.sample_source1], path=os.getcwd()
)
fake_non_empty_time_lapse_creator.nighttime_wait_before_next_retry = 1


def test_initializes_correctly_for_default_location(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    assert isinstance(sample_empty_time_lapse_creator.folder_name, str)
    assert isinstance(sample_empty_time_lapse_creator.location, LocationAndTimeManager)
    assert isinstance(sample_empty_time_lapse_creator.sources, set)
    assert isinstance(sample_empty_time_lapse_creator.location.city, LocationInfo)
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
    assert sample_empty_time_lapse_creator.video_width == DEFAULT_VIDEO_WIDTH
    assert sample_empty_time_lapse_creator.video_height == DEFAULT_VIDEO_HEIGHT


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
        argument = col([td.sample_source1, td.sample_source2])  # type: ignore

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
    result = sample_empty_time_lapse_creator.check_sources(td.sample_source1)  # type: ignore

    # Assert
    assert isinstance(result, Source)


def test_check_sources_returns_set_with_sources_if_valid_collections_are_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    allowed_collections = (set, list, tuple)

    # Act & Assert
    for col in allowed_collections:
        argument = col([td.sample_source1, td.sample_source2])  # type: ignore

        result = sample_empty_time_lapse_creator.check_sources(argument)  # type: ignore
        assert isinstance(result, set)


def test_add_sources_successfully_adds_one_source(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    sample_empty_time_lapse_creator.add_sources({td.sample_source1})

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 1


def test_add_sources_successfully_adds_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    result = sample_empty_time_lapse_creator.add_sources(
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3
    assert not result


def test_add_sources_doesnt_add_source_if_duplicate_name_or_url_is_found(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_empty_time_lapse_creator.add_sources({td.sample_source1})

    # Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.warning",
            return_value=None,
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
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.warning",
            return_value=None,
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
    ):
        result = sample_empty_time_lapse_creator.add_sources(
            {
                td.sample_source1,
                td.sample_source2,
                td.sample_source3,
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
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )

    # Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3

    sample_empty_time_lapse_creator.remove_sources(td.sample_source1)
    assert len(sample_empty_time_lapse_creator.sources) == 2


def test_remove_sources_successfully_removes_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange
    sample_empty_time_lapse_creator.add_sources(
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )

    # Act & Assert
    assert len(sample_empty_time_lapse_creator.sources) == 3

    result = sample_empty_time_lapse_creator.remove_sources(
        {td.sample_source1, td.sample_source2}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 1
    assert not result


def test_remove_sources_doesnt_remove_a_source_if_source_is_not_found(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.warning",
            return_value=None,
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
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
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.warning",
            return_value=None,
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.create_log_message",
            return_value="",
        ) as mock_util,
    ):
        result = sample_non_empty_time_lapse_creator.remove_sources(
            [td.sample_source1, td.non_existing_source]
        )

    # Assert
    assert mock_logger.call_count == 1
    assert mock_util.call_count == 1
    assert len(sample_non_empty_time_lapse_creator.sources) == 2
    assert not result


def test_verify_request_reraises_exception_if_url_is_invalid(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with pytest.raises(Exception):
        result = sample_non_empty_time_lapse_creator.verify_request(
            td.sample_source_with_empty_url
        )
        message = f"HTTPSConnectionPool(host='{td.sample_source_with_empty_url.url}', port=443): Max retries exceeded with url: / (Caused by NameResolutionError(\"<urllib3.connection.HTTPSConnection object at 0x00000144137B4500>: Failed to resolve '{td.sample_source_with_empty_url.url}' ([Errno 11001] getaddrinfo failed)\"))"
        assert result == message


def test_verify_request_reraises_exception_if_response_status_code_is_not_200(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    def mock_get(*args, **kwargs):  # type: ignore
        return tm.MockResponse()

    # Act
    monkeypatch.setattr(requests, "get", mock_get)  # type: ignore

    # Assert
    with pytest.raises(InvalidStatusCodeException):
        sample_non_empty_time_lapse_creator.verify_request(
            td.sample_source_with_empty_url
        )


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
        source.set_video_created()
        source.increase_images()

    # Act
    sample_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()

    # Assert
    for source in sample_non_empty_time_lapse_creator.sources:
        assert not source.video_created
        assert source.images_count == 0
        assert not source.images_collected
        assert not source.images_partially_collected


def test_create_video_returns_False_if_video_is_not_created(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.time_lapse_creator.vm.video_exists",
        return_value=True,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert not sample_non_empty_time_lapse_creator.create_video(source)
            assert not source.video_created


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
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_images",
            return_value=True,
        ) as mock_delete,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert len(sample_non_empty_time_lapse_creator.sources) == 3
            assert sample_non_empty_time_lapse_creator.create_video(source)
            assert not source.video_created

        assert mock_delete.call_count == 3


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
            "src.automatic_time_lapse_creator.time_lapse_creator.vm.delete_source_images",
            return_value=True,
        ) as mock_delete,
    ):
        for source in sample_non_empty_time_lapse_creator.sources:
            assert len(sample_non_empty_time_lapse_creator.sources) == 3
            assert sample_non_empty_time_lapse_creator.create_video(
                source, delete_source_images=False
            )
            assert not source.video_created

        assert mock_delete.call_count == 0


def test_collect_images_from_webcams_returns_False_if_not_daylight(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    monkeypatch.setattr(
        sample_non_empty_time_lapse_creator.location, "is_daylight", lambda: False
    )

    # Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.time_lapse_creator.logger.info",
        return_value=None,
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
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.info",
            return_value=None,
        ) as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.Path.mkdir",
            return_value=None,
        ),
        patch("builtins.open", mock_file),
    ):
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator.location, "is_daylight", mock_bool
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "verify_request", lambda: b"some_content"
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "cache_self", tm.mock_None
        )
        sample_non_empty_time_lapse_creator.wait_before_next_frame = 1

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
        patch("builtins.open", mock_file),
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.info",
            return_value=None,
        ) as mock_logger_info,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.logger.error",
            return_value=None,
        ) as mock_logger_error,
    ):
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator.location, "is_daylight", mock_bool
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "verify_request", lambda: Exception
        )
        monkeypatch.setattr(
            sample_non_empty_time_lapse_creator, "cache_self", lambda: None
        )
        sample_non_empty_time_lapse_creator.wait_before_next_frame = 1

        # Act & Assert
        assert sample_non_empty_time_lapse_creator.collect_images_from_webcams()
        assert mock_logger_info.call_count == 2
        assert mock_logger_error.call_count == 3


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
        patch(
            "src.automatic_time_lapse_creator.cache_manager.CacheManager.get",
            return_value=sample_non_empty_time_lapse_creator,
        ),
    ):
        sample_non_empty_time_lapse_creator.nighttime_wait_before_next_retry = 1
        sample_non_empty_time_lapse_creator.execute()

        # Assert
        mock_sleep.assert_called_once_with(
            sample_non_empty_time_lapse_creator.nighttime_wait_before_next_retry
        )


def test_execute_creates_video_for_every_source_when_all_images_are_collected():
    # Arrange, Act & Assert
    with (
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
            "src.automatic_time_lapse_creator.time_lapse_creator.dt"
        ) as mock_datetime,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.create_video",
            return_value=True,
        ) as mock_create_video,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.sleep",
            return_value=None,
        ) as mock_sleep,
    ):
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        fake_non_empty_time_lapse_creator.set_sources_all_images_collected()

        fake_non_empty_time_lapse_creator.execute()
        assert mock_sleep.call_count == 0
        assert mock_create_video.call_count == len(
            fake_non_empty_time_lapse_creator.sources
        )
        for source in fake_non_empty_time_lapse_creator.sources:
            mock_create_video.assert_called_once_with(source)
            assert source.video_created

        # Tear down
        fake_non_empty_time_lapse_creator.reset_test_counter()


def test_execute_creates_video_for_every_source_when_images_partially_collected():
    # Arrange, Act & Assert
    with (
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
            "src.automatic_time_lapse_creator.time_lapse_creator.dt"
        ) as mock_datetime,
        patch(
            "tests.test_time_lapse_creator.fake_non_empty_time_lapse_creator.create_video",
            return_value=True,
        ) as mock_create_video,
        patch(
            "src.automatic_time_lapse_creator.time_lapse_creator.sleep",
            return_value=None,
        ) as mock_sleep,
    ):
        mock_datetime.now.return_value = tm.MockDatetime.fake_nighttime
        fake_non_empty_time_lapse_creator.reset_all_sources_counters_to_default_values()

        for source in fake_non_empty_time_lapse_creator.sources:
            source.set_images_partially_collected()

        fake_non_empty_time_lapse_creator.execute()
        assert mock_collect.called
        assert mock_sleep.call_count == 0
        assert mock_create_video.call_count == len(
            fake_non_empty_time_lapse_creator.sources
        )
        for source in fake_non_empty_time_lapse_creator.sources:
            mock_create_video.assert_called_once_with(
                source, delete_source_images=False
            )
            assert source.video_created

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
    sample_cached_creator = TimeLapseCreator([td.sample_source1])
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
            patch(
                "src.automatic_time_lapse_creator.time_lapse_creator.logger.info",
                return_value=None,
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

    with patch("src.automatic_time_lapse_creator.time_lapse_creator.dt") as mock_today:
        mock_today.strptime.return_value = tm.MockDatetime.fake_today
        mock_today.today.return_value = tm.MockDatetime.fake_today
        sample_non_empty_time_lapse_creator.is_it_next_day()

        assert old_date == tm.MockDatetime.fake_today
        assert old_folder_name is sample_non_empty_time_lapse_creator.folder_name
        assert old_location is sample_non_empty_time_lapse_creator.location

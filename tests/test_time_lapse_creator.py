import pytest
import os

import requests
from src.automatic_time_lapse_creator_kokoeverest.common.constants import *
from src.automatic_time_lapse_creator_kokoeverest.source import Source
from src.automatic_time_lapse_creator_kokoeverest.time_lapse_creator import TimeLapseCreator
from src.automatic_time_lapse_creator_kokoeverest.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator_kokoeverest.common.exceptions import (
    InvalidStatusCodeException,
    InvalidCollectionException,
)
import tests.test_data as td
from datetime import datetime as dt
from astral import LocationInfo
from tests.test_mocks import MockResponse


@pytest.fixture
def sample_empty_time_lapse_creator():
    return TimeLapseCreator([])


@pytest.fixture
def sample_non_empty_time_lapse_creator():
    return TimeLapseCreator([td.sample_source1, td.sample_source1, td.sample_source3])


def test_initializes_correctly_for_default_location(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    assert isinstance(sample_empty_time_lapse_creator.folder_name, str)
    assert isinstance(sample_empty_time_lapse_creator.location, LocationAndTimeManager)
    assert isinstance(sample_empty_time_lapse_creator.sources, set)
    assert isinstance(sample_empty_time_lapse_creator.location.city, LocationInfo)
    assert sample_empty_time_lapse_creator.location.city.name == td.default_city_name
    assert sample_empty_time_lapse_creator.folder_name == dt.today().strftime(
        YYMMDD_FORMAT
    )
    assert sample_empty_time_lapse_creator.base_path == os.getcwd()
    assert len(sample_empty_time_lapse_creator.sources) == 0
    assert sample_empty_time_lapse_creator.wait_before_next_frame == 60
    assert sample_empty_time_lapse_creator.nighttime_wait_before_next_retry == 300
    assert sample_empty_time_lapse_creator.video_fps == 30
    assert sample_empty_time_lapse_creator.video_width == 640
    assert sample_empty_time_lapse_creator.video_height == 360


def test_sources_not_empty_returns_false_with_no_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    with pytest.raises(ValueError):
        result = sample_empty_time_lapse_creator.verify_sources_not_empty()
        assert result == "You should add at least one source for this location!"


def test_sources_not_empty_returns_true_when_source_is_added(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
    assert not sample_non_empty_time_lapse_creator.verify_sources_not_empty()


def test_check_sources_raises_InvalidCollectionEception_if_a_dict_is_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    empty_dict = {}
    with pytest.raises(InvalidCollectionException):
        result = sample_empty_time_lapse_creator._check_sources(empty_dict)  # type: ignore
        assert result == "Only list, tuple or set collections are allowed!"


def test_check_sources_returns_Source_if_a_single_valid_source_is_passed(
        sample_empty_time_lapse_creator: TimeLapseCreator,
):
    result = sample_empty_time_lapse_creator._check_sources(td.sample_source1) # type: ignore
    assert isinstance(result, Source)


def test_check_sources_returns_set_with_sources_if_valid_collections_are_passed(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    allowed_collections = (set, list, tuple)

    for col in allowed_collections:
        argument = col([td.sample_source1, td.sample_source2]) # type: ignore

        result = sample_empty_time_lapse_creator._check_sources(argument)  # type: ignore
        assert isinstance(result, set)


def test_add_sources_successfully_adds_one_source(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    sample_empty_time_lapse_creator.add_sources({td.sample_source1})
    assert len(sample_empty_time_lapse_creator.sources) == 1


def test_add_sources_successfully_adds_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    result = sample_empty_time_lapse_creator.add_sources(
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 3
    assert not result


def test_remove_sources_successfully_removes_a_single_source(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    sample_empty_time_lapse_creator.add_sources(
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 3

    sample_empty_time_lapse_creator.remove_sources(td.sample_source1)
    assert len(sample_empty_time_lapse_creator.sources) == 2


def test_remove_sources_successfully_removes_a_collection_of_sources(
    sample_empty_time_lapse_creator: TimeLapseCreator,
):
    sample_empty_time_lapse_creator.add_sources(
        {td.sample_source1, td.sample_source2, td.sample_source3}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 3

    result = sample_empty_time_lapse_creator.remove_sources(
        {td.sample_source1, td.sample_source2}
    )
    assert len(sample_empty_time_lapse_creator.sources) == 1
    assert not result


def test_verify_request_reraises_exception_if_url_is_invalid(
    sample_non_empty_time_lapse_creator: TimeLapseCreator,
):
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
    def mock_get(*args, **kwargs):  # type: ignore
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get) # type: ignore

    with pytest.raises(InvalidStatusCodeException):
        sample_non_empty_time_lapse_creator.verify_request(
            td.sample_source_with_empty_url
        )

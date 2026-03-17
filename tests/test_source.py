from queue import Queue
import pickle
import cv2
import numpy as np
import pytest
import tests.test_data as td
import tests.test_mocks as tm
from src.automatic_time_lapse_creator.source import (
    BrowserSource,
    ImageSource,
    StreamSource,
    Source,
)
from src.automatic_time_lapse_creator.common.constants import (
    YOUTUBE_URL_PREFIX,
    OK_STATUS_CODE,
)
from unittest.mock import MagicMock, Mock, patch
from requests import Response
from logging import Logger
from playwright.sync_api import Browser, Page


@pytest.fixture
def sample_source():
    return td.sample_source_no_weather_data


@pytest.fixture
def source_with_weather_provider():
    return tm.mock_source_with_weather_info_provider()


@pytest.fixture
def source_valid_video_stream():
    return tm.mock_source_valid_video_stream()


@pytest.fixture
def sample_StreamSource():
    return StreamSource(location_name="fake", url="fake_stream_url")


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=Logger)
    yield mock_logger
    mock_logger.reset_mock()


mock_log_queue = Mock(spec=Queue)


def test_source_initializes_correctly_with_default_config(mock_logger: Mock):
    # Arrange, Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch(
            "src.automatic_time_lapse_creator.source.ImageSource.validate_url",
            return_value=True,
        ) as mock_validate,
    ):
        sample_source = ImageSource(
            td.valid_source_name, td.valid_url
        )
        assert isinstance(sample_source, Source)
        assert sample_source.location_name == td.valid_source_name
        assert sample_source.url == td.valid_url
        assert not sample_source.daily_video_created
        assert not sample_source.monthly_video_created
        assert sample_source.images_count == 0
        assert not sample_source.images_collected
        assert not sample_source.images_partially_collected
        assert sample_source.is_valid_url
        assert not sample_source.weather_data_on_images
        assert not sample_source.weather_data_provider
        assert mock_logger.call_count == 0

        mock_validate.assert_called_with(sample_source.url)


def test_source_initializes_correctly_with_weather_data_provider(mock_logger: Logger):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.ImageSource.validate_url",
            return_value=True,
        ),
    ):
        actual_result = ImageSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
            weather_data_provider=tm.mock_source_with_weather_info_provider(),
        )

    # Assert
    assert actual_result.is_valid_url
    assert not actual_result.weather_data_on_images
    assert actual_result.weather_data_provider
    assert mock_logger.call_count == 1


def test_source_initializes_correctly_for_video_stream(mock_logger: Logger):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=True,
        ),
    ):
        actual_result = StreamSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
        )

    # Assert
    assert actual_result.is_valid_url
    assert not actual_result.weather_data_on_images
    assert not actual_result.weather_data_provider
    assert mock_logger.call_count == 0


def test_source_sets_is_valid_stream_to_False_for_invalid_video_stream(
    mock_logger: Logger,
):
    # Arrange, Act
    with (
        patch(
            "src.automatic_time_lapse_creator.source.configure_child_logger",
            return_value=mock_logger,
        ),
        patch.object(mock_logger, "info") as mock_logger,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=False,
        ),
    ):
        actual_result = StreamSource(
            location_name=td.valid_source_name,
            url=td.valid_url,
        )

    # Assert
    assert not actual_result.is_valid_url
    assert not actual_result.weather_data_on_images
    assert not actual_result.weather_data_provider
    assert mock_logger.call_count == 0


def test_set_video_created_changes_video_created_to_True(sample_source: Source):
    # Arrange & Act
    sample_source.set_daily_video_created()

    # Assert
    assert sample_source.daily_video_created


def test_reset_video_created_changes_video_created_to_False(sample_source: Source):
    # Arrange & Act
    sample_source.reset_daily_video_created()

    # Assert
    assert not sample_source.daily_video_created


def test_set_monthly_video_created_changes_monthly_video_created_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_monthly_video_created()

    # Assert
    assert sample_source.monthly_video_created


def test_reset_monthly_video_created_changes_monthly_video_created_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_monthly_video_created()

    # Assert
    assert not sample_source.monthly_video_created


def test_set_videos_count_sets_the_value(sample_source: Source):
    # Arrange & Act
    video_files_count = 12
    sample_source.set_videos_count(video_files_count)

    # Assert
    assert sample_source.daily_videos_count == video_files_count


def test_reset_daily_videos_counter_resets_to_zero(sample_source: Source):
    # Arrange & Act
    sample_source.reset_daily_videos_counter()

    # Assert
    assert sample_source.daily_videos_count == 0


def test_increase_images_increases_the_images_count_by_one(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()

    # Assert
    assert sample_source.images_count == 1


def test_reset_images_counter_resets_the_images_count_to_zero(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()
    sample_source.reset_images_counter()

    # Assert
    assert sample_source.images_count == 0


def test_set_all_images_collected_sets_all_images_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_all_images_collected()

    # Assert
    assert sample_source.images_collected


def test_reset_all_images_collected_resets_all_images_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_all_images_collected()

    # Assert
    assert not sample_source.images_collected


def test_set_images_partially_collected_sets_images_partially_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_images_partially_collected()

    # Assert
    assert sample_source.images_partially_collected


def test_reset_images_partially_collected_resets_images_partially_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_images_partially_collected()

    # Assert
    assert not sample_source.images_partially_collected


def test_validate_stream_url_returns_True_if_url_is_valid_stream(
    sample_StreamSource: StreamSource, mock_logger: Mock
):
    # Arrange
    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.get_url_with_yt_dlp",
            return_value="",
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = (True, tm.mock_MatLike)
        mock_cap_instance.release.return_value = None

        # Act
        actual_result = sample_StreamSource.validate_url(
            sample_StreamSource.url
        )

        # Assert
        mock_cap_instance.read.assert_called()
        mock_cap_instance.release.assert_called()
        mock_logger.warning.assert_not_called()
        assert actual_result


def test_validate_stream_url_returns_False_if_url_is_invalid_stream(
    sample_StreamSource: StreamSource,
    mock_logger: Mock,
):
    # Arrange
    invalid_url_return = "mock_invalid_url"
    sample_StreamSource.logger = mock_logger
    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch.object(
            StreamSource,
            "get_url_with_yt_dlp",
            return_value=invalid_url_return,
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = (False, None)

        # Act
        actual_result = sample_StreamSource.validate_url(
            YOUTUBE_URL_PREFIX
        )

        # Assert
        assert not actual_result
        sample_StreamSource.logger.warning.assert_called_once_with(
            f"{sample_StreamSource.location_name}: {invalid_url_return} is not a valid url and will be ignored!"
        )


def test_validate_stream_url_returns_False_if_Exception_occured(
    sample_StreamSource: StreamSource, mock_logger: Mock
):
    sample_StreamSource.logger = mock_logger
    # Arrange
    invalid_url_return = "mock_invalid_url"

    with (
        patch(
            "cv2.VideoCapture",
        ) as mock_cap,
        patch.object(
            StreamSource,
            "get_url_with_yt_dlp",
            return_value=invalid_url_return,
        ),
    ):
        mock_cap_instance = mock_cap.return_value
        mock_cap_instance.read.return_value = Exception

        # Act
        actual_result = sample_StreamSource.validate_url(
            YOUTUBE_URL_PREFIX
        )

        # Assert
        assert not actual_result
        mock_logger.error.assert_called_once()


def test_validate_url_returns_False_if_Exception_occured(
    sample_source: ImageSource, mock_logger: Mock
):
    # Arrange
    sample_source.logger = mock_logger
    with patch("requests.get", side_effect=Exception):
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert not actual_result
        mock_logger.error.assert_called_once()


def test_validate_url_returns_False_if_returned_content_is_not_bytes(
    sample_source: ImageSource,
    mock_logger: Mock,
):
    # Arrange
    sample_source.logger = mock_logger
    with (
        patch("requests.get", return_value=Mock(spec=Response)) as mock_response,
    ):
        mock_response.content = "<html>"
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert not actual_result
        mock_logger.warning.assert_called_once()


def test_validate_url_returns_True_if_returned_content_is_bytes(
    sample_source: ImageSource, mock_logger: Mock
):
    # Arrange
    sample_source.logger = mock_logger
    mock_response = Mock(spec=Response)
    mock_response.status_code = OK_STATUS_CODE
    mock_response.content = b"some_content"
    with patch("requests.get", return_value=mock_response):
        # Act
        actual_result = sample_source.validate_url(YOUTUBE_URL_PREFIX)

        # Assert
        assert actual_result
        mock_logger.info.assert_called_once()


def test_get_frame_bytes_returns_correct_result_for_ImageSource(
    sample_source: ImageSource,
):
    # Arrange
    expected_result = b"some content"
    with patch.object(
        sample_source, "get_frame_bytes", return_value=expected_result
    ) as mock_source:
        # Act
        actual_result = sample_source.get_frame_bytes()

    # Assert
    assert actual_result == expected_result
    mock_source.assert_called_once()
    assert mock_source.fetch_image_from_stream.call_count == 0


def test_get_frame_bytes_returns_correct_result_for_StreamSource(
    sample_StreamSource: StreamSource
):
    # Arrange
    expected_result = b"some content"
    with (
        patch.object(
            sample_StreamSource,
            "get_frame_bytes",
            return_value=expected_result,
        ) as mock_source,
        patch(
            "src.automatic_time_lapse_creator.source.StreamSource.validate_url",
            return_value=True,
        ),
    ):
        # Act
        actual_result = sample_StreamSource.get_frame_bytes()

    # Assert
    mock_source.assert_called_once()
    assert mock_source.fetch_image_from_static_web_cam.call_count == 0
    assert actual_result == expected_result


# ---------------------------------------------------------------------------
# BrowserSource fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_BrowserSource(mock_logger: Mock):
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        source = BrowserSource(
            location_name="fake_browser",
            url="https://example.com/webcam",
        )
    source.logger = mock_logger
    return source


@pytest.fixture
def sample_BrowserSource_with_selector(mock_logger: Mock):
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        source = BrowserSource(
            location_name="fake_browser_sel",
            url="https://example.com/webcam",
            selector="#my-webcam video",
        )
    source.logger = mock_logger
    return source


@pytest.fixture
def sample_BrowserSource_persistent(mock_logger: Mock):
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        source = BrowserSource(
            location_name="fake_browser_persistent",
            url="https://example.com/webcam",
            persistent_session=True,
        )
    source.logger = mock_logger
    return source


# ---------------------------------------------------------------------------
# BrowserSource – initialisation
# ---------------------------------------------------------------------------

def test_browser_source_initializes_without_selector(
    sample_BrowserSource: BrowserSource,
):
    assert isinstance(sample_BrowserSource, Source)
    assert sample_BrowserSource.selector is None
    assert sample_BrowserSource.url == "https://example.com/webcam"
    assert sample_BrowserSource.location_name == "fake_browser"
    assert sample_BrowserSource.persistent_session is False


def test_browser_source_initializes_with_selector(
    sample_BrowserSource_with_selector: BrowserSource,
):
    assert sample_BrowserSource_with_selector.selector == "#my-webcam video"


def test_browser_source_initializes_with_persistent_session(
    sample_BrowserSource_persistent: BrowserSource,
):
    assert sample_BrowserSource_persistent.persistent_session is True
    assert sample_BrowserSource_persistent._pw is None
    assert sample_BrowserSource_persistent._browser is None
    assert sample_BrowserSource_persistent._page is None


# ---------------------------------------------------------------------------
# BrowserSource – validate_url
# ---------------------------------------------------------------------------

def test_validate_url_returns_True_when_screenshot_succeeds(
    sample_BrowserSource: BrowserSource, mock_logger: Mock
):
    with patch.object(
        sample_BrowserSource,
        "_capture_screenshot",
        return_value=b"fake_jpeg_bytes",
    ):
        result = sample_BrowserSource.validate_url(sample_BrowserSource.url)

    assert result is True
    mock_logger.info.assert_called_once()


def test_validate_url_returns_False_when_no_element_found(
    sample_BrowserSource: BrowserSource, mock_logger: Mock
):
    with patch.object(
        sample_BrowserSource,
        "_capture_screenshot",
        return_value=None,
    ):
        result = sample_BrowserSource.validate_url(sample_BrowserSource.url)

    assert result is False
    mock_logger.info.assert_not_called()


def test_validate_url_returns_False_on_exception(
    sample_BrowserSource: BrowserSource, mock_logger: Mock
):
    with patch.object(
        sample_BrowserSource,
        "_capture_screenshot",
        side_effect=Exception("connection refused"),
    ):
        result = sample_BrowserSource.validate_url(sample_BrowserSource.url)

    assert result is False
    mock_logger.error.assert_called_once()


# ---------------------------------------------------------------------------
# BrowserSource – get_frame_bytes
# ---------------------------------------------------------------------------

def test_get_frame_bytes_returns_bytes_on_success(
    sample_BrowserSource: BrowserSource,
):
    expected = b"jpeg_frame_bytes"
    with patch.object(
        sample_BrowserSource,
        "_capture_screenshot",
        return_value=expected,
    ):
        result = sample_BrowserSource.get_frame_bytes()

    assert result == expected


def test_get_frame_bytes_returns_None_when_no_element_found(
    sample_BrowserSource: BrowserSource,
):
    with patch.object(
        sample_BrowserSource,
        "_capture_screenshot",
        return_value=None,
    ):
        result = sample_BrowserSource.get_frame_bytes()

    assert result is None


def test_get_frame_bytes_raises_on_exception(
    sample_BrowserSource: BrowserSource,
):
    with (
        patch.object(
            sample_BrowserSource,
            "_capture_screenshot",
            side_effect=RuntimeError("browser crashed"),
        ),
        pytest.raises(RuntimeError, match="browser crashed"),
    ):
        sample_BrowserSource.get_frame_bytes()


# ---------------------------------------------------------------------------
# BrowserSource – _find_element (auto-detection)
# ---------------------------------------------------------------------------

def _make_mock_element(width: float = 100, height: float = 100, visible: bool = True):
    el = MagicMock()
    el.is_visible.return_value = visible
    el.bounding_box.return_value = {"width": width, "height": height}
    return el


def test_find_element_uses_explicit_selector(
    sample_BrowserSource_with_selector: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    expected_el = _make_mock_element()
    mock_page.wait_for_selector.return_value = expected_el

    result = sample_BrowserSource_with_selector._find_element(mock_page)

    mock_page.wait_for_selector.assert_called_once_with(
        "#my-webcam video",
        state="visible",
        timeout=15000,
    )
    assert result is expected_el


def test_find_element_auto_detects_video_element(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    video_el = _make_mock_element(640, 480)

    def query_selector_all(sel: str):
        return [video_el] if sel == "video" else []

    mock_page.query_selector_all.side_effect = query_selector_all

    result = sample_BrowserSource._find_element(mock_page)

    assert result is video_el


def test_find_element_picks_largest_element(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    small = _make_mock_element(100, 100)
    large = _make_mock_element(1280, 720)

    mock_page.query_selector_all.side_effect = lambda sel: (  # type: ignore
        [small, large] if sel == "video" else []
    )

    result = sample_BrowserSource._find_element(mock_page)

    assert result is large


def test_find_element_skips_invisible_elements(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    invisible = _make_mock_element(visible=False)
    canvas_el = _make_mock_element(800, 600)

    def query_selector_all(sel: str) -> list[MagicMock]:
        """Return a list of elements matching the selector."""
        if sel == "video":
            return [invisible]
        if sel == "canvas":
            return [canvas_el]
        return []

    mock_page.query_selector_all.side_effect = query_selector_all

    result = sample_BrowserSource._find_element(mock_page)

    assert result is canvas_el


def test_find_element_returns_None_when_nothing_found(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    mock_page.query_selector_all.return_value = []

    result = sample_BrowserSource._find_element(mock_page)

    assert result is None


# ---------------------------------------------------------------------------
# BrowserSource – blank frame detection (_is_blank_frame / _screenshot_page)
# ---------------------------------------------------------------------------

def _make_jpeg(brightness: int) -> bytes:
    """Return a valid JPEG-encoded image filled with the given grey brightness."""
    img = np.full((100, 100, 3), brightness, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ---------------------------------------------------------------------------
# BrowserSource – popup dismissal (_dismiss_popups)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_BrowserSource_with_dismiss(mock_logger: Mock):
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        source = BrowserSource(
            location_name="fake_browser_dismiss",
            url="https://example.com/webcam",
            dismiss_selectors=[
                "button:has-text('Accept')",
                "button.close-popup",
            ],
        )
    source.logger = mock_logger
    return source


def test_dismiss_selectors_property(
    sample_BrowserSource_with_dismiss: BrowserSource,
):
    assert sample_BrowserSource_with_dismiss.dismiss_selectors == [
        "button:has-text('Accept')",
        "button.close-popup",
    ]


def test_dismiss_selectors_defaults_to_empty_list(
    sample_BrowserSource: BrowserSource,
):
    assert sample_BrowserSource.dismiss_selectors == []


def test_dismiss_popups_clicks_each_selector(
    sample_BrowserSource_with_dismiss: BrowserSource,
):
    mock_page = MagicMock(spec=Page)

    sample_BrowserSource_with_dismiss._dismiss_popups(mock_page)

    assert mock_page.click.call_count == 2
    mock_page.click.assert_any_call(
        "button:has-text('Accept')",
        timeout=BrowserSource.DISMISS_TIMEOUT_MS,
    )
    mock_page.click.assert_any_call(
        "button.close-popup",
        timeout=BrowserSource.DISMISS_TIMEOUT_MS,
    )


def test_dismiss_popups_silently_skips_missing_elements(
    sample_BrowserSource_with_dismiss: BrowserSource, mock_logger: Mock
):
    mock_page = MagicMock(spec=Page)
    mock_page.click.side_effect = Exception("element not found")

    # Should not raise even when every click fails
    sample_BrowserSource_with_dismiss._dismiss_popups(mock_page)


def test_dismiss_popups_is_noop_with_empty_list(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)

    sample_BrowserSource._dismiss_popups(mock_page)

    mock_page.click.assert_not_called()


def test_ensure_page_calls_dismiss_popups(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_pw_instance, _, mock_page = _make_persistent_mocks()

    with (
        patch(
            "src.automatic_time_lapse_creator.source.sync_playwright"
        ) as mock_sync_playwright,
        patch.object(
            sample_BrowserSource_persistent, "_dismiss_popups"
        ) as mock_dismiss,
    ):
        mock_sync_playwright.return_value.start.return_value = mock_pw_instance

        sample_BrowserSource_persistent._ensure_page()

    mock_dismiss.assert_called_once_with(mock_page)


# ---------------------------------------------------------------------------
# BrowserSource – blank frame detection (_is_blank_frame / _screenshot_page)
# ---------------------------------------------------------------------------

def test_is_blank_frame_returns_True_for_black_image(
    sample_BrowserSource: BrowserSource,
):
    assert sample_BrowserSource._is_blank_frame(_make_jpeg(0)) is True


def test_is_blank_frame_returns_False_for_bright_image(
    sample_BrowserSource: BrowserSource,
):
    assert sample_BrowserSource._is_blank_frame(_make_jpeg(128)) is False


def test_is_blank_frame_returns_False_when_threshold_is_zero(
    sample_BrowserSource: BrowserSource,
):
    original = BrowserSource.BLANK_BRIGHTNESS_THRESHOLD
    try:
        BrowserSource.BLANK_BRIGHTNESS_THRESHOLD = 0
        assert sample_BrowserSource._is_blank_frame(_make_jpeg(0)) is False
    finally:
        BrowserSource.BLANK_BRIGHTNESS_THRESHOLD = original


def test_screenshot_page_returns_None_for_blank_frame(
    sample_BrowserSource: BrowserSource, mock_logger: Mock
):
    mock_page = MagicMock(spec=Page)
    mock_element = _make_mock_element()
    mock_page.wait_for_selector.return_value = mock_element
    sample_BrowserSource.selector = "#cam"
    mock_element.screenshot.return_value = _make_jpeg(0)

    result = sample_BrowserSource._screenshot_page(mock_page)

    assert result is None
    mock_logger.debug.assert_called_once()


def test_screenshot_page_returns_bytes_for_non_blank_frame(
    sample_BrowserSource: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    mock_element = _make_mock_element()
    mock_page.wait_for_selector.return_value = mock_element
    sample_BrowserSource.selector = "#cam"
    jpeg = _make_jpeg(128)
    mock_element.screenshot.return_value = jpeg

    result = sample_BrowserSource._screenshot_page(mock_page)

    assert result == jpeg


# ---------------------------------------------------------------------------
# BrowserSource – persistent session (_ensure_page / close)
# ---------------------------------------------------------------------------

def _make_persistent_mocks():
    """Return a mock Playwright stack: (mock_pw_start, mock_browser, mock_page)."""
    mock_page = MagicMock(spec=Page)
    mock_browser = MagicMock(spec=Browser)
    mock_browser.is_connected.return_value = True
    mock_browser.new_page.return_value = mock_page

    mock_pw_instance = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser

    return mock_pw_instance, mock_browser, mock_page


def test_ensure_page_opens_browser_on_first_call(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_pw_instance, mock_browser, mock_page = _make_persistent_mocks()

    with patch(
        "src.automatic_time_lapse_creator.source.sync_playwright"
    ) as mock_sync_playwright:
        mock_sync_playwright.return_value.start.return_value = mock_pw_instance

        page = sample_BrowserSource_persistent._ensure_page()

    assert page is mock_page
    mock_page.goto.assert_called_once_with(
        sample_BrowserSource_persistent.url,
        timeout=BrowserSource.PAGE_LOAD_TIMEOUT_MS,
        wait_until="load",
    )
    assert sample_BrowserSource_persistent._browser is mock_browser
    assert sample_BrowserSource_persistent._page is mock_page


def test_ensure_page_reuses_existing_page(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_pw_instance, mock_browser, mock_page = _make_persistent_mocks()

    sample_BrowserSource_persistent._pw = mock_pw_instance
    sample_BrowserSource_persistent._browser = mock_browser
    sample_BrowserSource_persistent._page = mock_page

    with patch(
        "src.automatic_time_lapse_creator.source.sync_playwright"
    ) as mock_sync_playwright:
        page = sample_BrowserSource_persistent._ensure_page()

    mock_sync_playwright.assert_not_called()
    mock_page.goto.assert_not_called()
    assert page is mock_page


def test_ensure_page_reopens_after_disconnect(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_pw_instance, _, mock_page = _make_persistent_mocks()

    disconnected_browser = MagicMock(spec=Browser)
    disconnected_browser.is_connected.return_value = False
    sample_BrowserSource_persistent._browser = disconnected_browser
    sample_BrowserSource_persistent._page = mock_page

    with patch(
        "src.automatic_time_lapse_creator.source.sync_playwright"
    ) as mock_sync_playwright:
        mock_sync_playwright.return_value.start.return_value = mock_pw_instance

        page = sample_BrowserSource_persistent._ensure_page()

    assert page is mock_page
    mock_page.goto.assert_called_once()


def test_capture_screenshot_uses_ensure_page_in_persistent_mode(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_page = MagicMock(spec=Page)
    expected = b"persistent_jpeg"

    with (
        patch.object(
            sample_BrowserSource_persistent,
            "_ensure_page",
            return_value=mock_page,
        ) as mock_ensure,
        patch.object(
            sample_BrowserSource_persistent,
            "_screenshot_page",
            return_value=expected,
        ) as mock_screenshot,
    ):
        result = sample_BrowserSource_persistent._capture_screenshot(
            sample_BrowserSource_persistent.url
        )

    mock_ensure.assert_called_once()
    mock_screenshot.assert_called_once_with(mock_page)
    assert result == expected


def test_close_releases_persistent_session(
    sample_BrowserSource_persistent: BrowserSource,
):
    mock_pw_instance, mock_browser, mock_page = _make_persistent_mocks()

    sample_BrowserSource_persistent._pw = mock_pw_instance
    sample_BrowserSource_persistent._browser = mock_browser
    sample_BrowserSource_persistent._page = mock_page

    sample_BrowserSource_persistent.close()

    mock_browser.close.assert_called_once()
    mock_pw_instance.stop.assert_called_once()
    assert sample_BrowserSource_persistent._browser is None
    assert sample_BrowserSource_persistent._page is None
    assert sample_BrowserSource_persistent._pw is None


def test_close_is_noop_when_session_never_opened(
    sample_BrowserSource_persistent: BrowserSource,
):
    # Should not raise even though nothing was ever opened
    sample_BrowserSource_persistent.close()

    assert sample_BrowserSource_persistent._browser is None
    assert sample_BrowserSource_persistent._pw is None


def test_close_is_noop_for_ephemeral_source(
    sample_BrowserSource: BrowserSource,
):
    sample_BrowserSource.close()  # should not raise


# ---------------------------------------------------------------------------
# BrowserSource – pickle / CacheManager compatibility
# ---------------------------------------------------------------------------
# These fixtures use real Logger objects instead of MagicMock because
# MagicMock(spec=Logger) tricks pickle's __newobj__ protocol into a class
# mismatch error that is irrelevant to the behaviour under test.

@pytest.fixture
def browser_source_for_pickle():
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        return BrowserSource(
            location_name="fake_browser_pickle",
            url="https://example.com/webcam",
        )


@pytest.fixture
def persistent_browser_source_for_pickle():
    with patch(
        "src.automatic_time_lapse_creator.source.BrowserSource.validate_url",
        return_value=True,
    ):
        return BrowserSource(
            location_name="fake_browser_pickle_persistent",
            url="https://example.com/webcam",
            persistent_session=True,
        )


def test_ephemeral_browser_source_is_picklable(
    browser_source_for_pickle: BrowserSource,
):
    data = pickle.dumps(browser_source_for_pickle)
    restored = pickle.loads(data)

    assert restored.location_name == browser_source_for_pickle.location_name
    assert restored.url == browser_source_for_pickle.url
    assert restored.persistent_session is False
    assert restored._pw is None
    assert restored._browser is None
    assert restored._page is None


def test_persistent_browser_source_is_picklable_with_live_session(
    persistent_browser_source_for_pickle: BrowserSource,
):
    mock_pw_instance, mock_browser, mock_page = _make_persistent_mocks()
    persistent_browser_source_for_pickle._pw = mock_pw_instance
    persistent_browser_source_for_pickle._browser = mock_browser
    persistent_browser_source_for_pickle._page = mock_page

    data = pickle.dumps(persistent_browser_source_for_pickle)
    restored = pickle.loads(data)

    assert restored.location_name == persistent_browser_source_for_pickle.location_name
    assert restored.persistent_session is True
    # Live Playwright objects must be stripped — session will reopen lazily
    assert restored._pw is None
    assert restored._browser is None
    assert restored._page is None

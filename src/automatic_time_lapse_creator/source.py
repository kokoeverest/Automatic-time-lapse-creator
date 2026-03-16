from abc import ABC, abstractmethod
import concurrent.futures
import cv2
import subprocess
import requests
from logging import Logger
from playwright.sync_api import sync_playwright, Browser, ElementHandle, Page, Playwright
from typing import Any
from time import sleep
from .common.logger import configure_child_logger
from .common.constants import OK_STATUS_CODE
from .common.exceptions import InvalidStatusCodeException
from .weather_station_info import WeatherStationInfo


class Source(ABC):
    """
    This abstract base class defines the common methods and properties for a Source. It provides
    functionality for retrieving images, validating video streams, and managing metadata
    such as the number of collected images and video creation status.

    Attributes:
        location_name: str - The name of the location. This is used for organizing
            the images and videos into appropriate folders.

        url: str - The URL of the webcam feed (it should poit to either an image resource or a video stream).

        weather_data_on_images: bool - Set this to True if the images already have weather data
        on them

        weather_data_provider: WeatherStationInfo | None - An optional provider for retrieving weather data to overlay on images.
        #### *weather_data_provider will be ignored if the weather_data_on_images is set to True in order to avoid duplicate data.*

        owner: str | None - Optionally you can provide the name of identifier of the owner of the source.

        _is_valid_url: bool - Whether the provided URL is a valid for collecting images from.
        _has_weather_data: bool - Whether weather data should be included in images.
        _daily_video_created: bool - Indicates whether a daily video has been successfully created.
        _monthly_video_created: bool - Indicates whether a monthly video has been successfully created.
        _images_count: int - Tracks the number of images collected from the source.
        _all_images_collected: bool - Flag indicating whether all images have been
            collected for a specific period.
        _images_partially_collected: bool - Flag indicating whether images were
            only partially collected due to interruptions.
    """

    def __init__(
        self,
        location_name: str,
        url: str,
        logger: Logger | None = None,
        weather_data_on_images: bool = False,
        weather_data_provider: WeatherStationInfo | None = None,
        owner: str | None = None,
        skip_validation: bool = False,
    ) -> None:
        self.location_name = location_name
        self.url = url
        if logger is not None:
            self.logger = logger
        else:
            self.logger = configure_child_logger(logger_name=self.location_name, logger=logger)

        self._is_valid_url = self.validate_url(url) if not skip_validation else True

        self._has_weather_data = weather_data_on_images
        if self._has_weather_data and weather_data_provider is not None:
            self.logger.warning(
                "Weather data on images is set to True!\nWeather data provider will be ignored to avoid duplicate data on images!"
            )
            self.weather_data_provider = None
        else:
            self.weather_data_provider = weather_data_provider
            if not self.weather_data_on_images and self.weather_data_provider is not None:
                self.logger.info(f"Weather provider set for {self.location_name}")
        self.owner = owner
        self._daily_video_created: bool = False
        self._monthly_video_created: bool = False
        self._images_count: int = 0
        self._daily_videos_count: int = 0
        self._all_images_collected: bool = False
        self._images_partially_collected: bool = False

    @property
    def weather_data_on_images(self) -> bool:
        """
        If weather data is originally available on the images for the given url.

        Returns:
            bool: True if weather data exists on images, otherwise False.
        """
        return self._has_weather_data

    @property
    def is_valid_url(self) -> bool:
        """
        Checks whether the provided URL is valid.

        Returns:
            bool: True if the URL returns bytes content, otherwise False.
        """
        return self._is_valid_url

    @property
    def images_collected(self) -> bool:
        """
        Indicates whether all expected images have been collected.

        Returns:
            bool: True if all images have been collected, otherwise False.
        """
        return self._all_images_collected

    @property
    def images_partially_collected(self) -> bool:
        """
        Indicates whether only a portion of the expected images have been collected.
        This will happen if the execute() method of the TimeLapseCreator is killed
        prematurely.

        Returns:
            bool: True if images were partially collected, otherwise False.
        """
        return self._images_partially_collected

    @property
    def images_count(self) -> int:
        """
        Retrieves the number of images collected from this source.

        Returns:
            int: The total number of images collected.
        """
        return self._images_count
    
    @property
    def daily_videos_count(self) -> int:
        """
        Retrieves the number of daily videos collected from this source 
        and used for creation of a monthly summary video.

        Returns:
            int: The total number of videos collected.
        """
        return self._daily_videos_count

    @property
    def daily_video_created(self) -> bool:
        """
        Indicates whether a video has been successfully created from the collected images.

        Returns:
            bool: True if a video has been created, otherwise False.
        """
        return self._daily_video_created

    @property
    def monthly_video_created(self) -> bool:
        """
        Indicates whether a monthly summary video has been successfully created from the existing daily videos.

        Returns:
            bool: True if a video has been created, otherwise False.
        """
        return self._monthly_video_created

    def set_daily_video_created(self) -> None:
        """Set the daily_video_created to True"""
        self._daily_video_created = True

    def reset_daily_video_created(self) -> None:
        """Reset the daily_video_created to False"""
        self._daily_video_created = False

    def set_monthly_video_created(self) -> None:
        """Set the monthly_video_created to True"""
        self._monthly_video_created = True

    def reset_monthly_video_created(self) -> None:
        """Reset the monthly_video_created to False"""
        self._monthly_video_created = False

    def increase_images(self) -> None:
        """Increases the count of the images by 1"""
        self._images_count += 1

    def reset_images_counter(self) -> None:
        """Resets the images count to 0"""
        self._images_count = 0

    def set_videos_count(self, count: int) -> None:
        """Set the count of the daily videos to the specified count"""
        self._daily_videos_count = count

    def reset_daily_videos_counter(self) -> None:
        """Resets the daily videos count to 0"""
        self._daily_videos_count = 0

    def set_all_images_collected(self) -> None:
        """Sets the self._all_images_collected to True"""
        self._all_images_collected = True

    def set_images_partially_collected(self) -> None:
        """Sets the self._images_partially_collected to True"""
        self._images_partially_collected = True

    def reset_all_images_collected(self) -> None:
        """Resets the self._all_images_collected to False"""
        self._all_images_collected = False

    def reset_images_partially_collected(self) -> None:
        """Resets the self._images_partially_collected to False"""
        self._images_partially_collected = False

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        pass

    @abstractmethod
    def get_frame_bytes(self) -> bytes | None:
        pass


class ImageSource(Source):
    """Represents a static webcam source for capturing image frames."""
    def validate_url(self, url: str) -> bool:
        """Verifies the provided url will return bytes content.

        Returns::
            bool - if the response returns bytes content.
        """

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except Exception as exc:
            self.logger.error(
                f"Something went wrong during check of url {url}! Maybe it points to a video stream?\n({exc})"
            )
            return False
        if isinstance(response.content, bytes):
            self.logger.info(f"{self.location_name} has a valid url for collecting images")
            return True
        else:
            self.logger.warning(f"{url} is NOT a valid source for collecting images")
            return False

    def get_frame_bytes(self) -> bytes | None:
        """Verifies the request status code is 200  and returns the response content as bytes.

        Raises::

            InvalidStatusCodeException if the code is different,
            because request.content would not be accessible and the program will crash.

        Returns::
            bytes | Any - the content of the response if Exception is not raised."""

        try:
            response = requests.get(self.url, timeout=15)
            if response.status_code != OK_STATUS_CODE:
                raise InvalidStatusCodeException(
                    f"Status code {response.status_code} is not {OK_STATUS_CODE} for url {self.url}"
                )
        except Exception as exc:
            self.logger.error(f"{self.location_name}: {exc}")
            raise exc
        return response.content


class StreamSource(Source):
    """Represents a webcam source for capturing images from a video stream."""

    OPEN_TIMEOUT_MS: int = 15_000
    READ_TIMEOUT_MS: int = 15_000
    # Hard wall-clock timeout (seconds) for the entire open+read operation.
    # CAP_PROP_*_TIMEOUT_MSEC may not be honoured by every backend/protocol,
    # so we enforce this at the Python level via a thread executor.
    CAPTURE_WALL_TIMEOUT_S: float = 30.0

    @staticmethod
    def get_url_with_yt_dlp(url: str) -> str:
        """Use yt-dlp to extract the direct URL"""

        command = ["yt-dlp", "-g", "--format", "best", url]
        result = subprocess.run(command, capture_output=True, text=True)
        video_url = result.stdout.strip()
        return video_url

    @staticmethod
    def _open_capture(url: str) -> cv2.VideoCapture:
        """
        Opens a VideoCapture for the given URL with explicit open/read timeouts.

        Uses the two-step VideoCapture() + open() pattern so that the timeout
        properties are registered with the backend before the network connection
        is attempted (the single-argument constructor opens immediately, leaving
        no opportunity to set properties first).
        """
        cap = cv2.VideoCapture()
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, StreamSource.OPEN_TIMEOUT_MS)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, StreamSource.READ_TIMEOUT_MS)
        cap.open(url)
        return cap

    def _read_frame(self, url: str) -> tuple[bool, cv2.typing.MatLike | None]:
        """
        Opens the stream and reads one frame, entirely within a thread so that
        a hard wall-clock timeout can be enforced even when the backend ignores
        the CAP_PROP_*_TIMEOUT_MSEC properties.

        Returns the (ret, frame) tuple from cap.read(), or (False, None) on any
        error or timeout.
        """
        def _capture() -> tuple[bool, cv2.typing.MatLike | None]:
            cap = self._open_capture(url)
            try:
                return cap.read()
            finally:
                cap.release()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_capture)
            try:
                return future.result(timeout=self.CAPTURE_WALL_TIMEOUT_S)
            except concurrent.futures.TimeoutError:
                self.logger.warning(
                    f"{self.location_name}: stream capture timed out after "
                    f"{self.CAPTURE_WALL_TIMEOUT_S}s"
                )
                return False, None

    def validate_url(self, url: str) -> bool:
        """
        Validates if the given URL is a valid video stream.

        If the URL is a YouTube link, it attempts to retrieve a direct video stream URL
        using `yt-dlp`. Then, OpenCV tries to open the stream and check if frames can be read.

        Args:
            url: str - The URL of the video stream.

        Returns:
            bool: True if the URL is a valid video stream, otherwise False.
        """
        _url = self.get_url_with_yt_dlp(url) if "youtube.com/watch?v=" in url else url

        try:
            ret, _ = self._read_frame(_url)
            if not ret:
                self.logger.warning(
                    f"{self.location_name}: {_url} is not a valid url and will be ignored!"
                )
                return False

            self.logger.info(f"{self.location_name} has a valid stream url for collecting images")
            return True

        except Exception as e:
            self.logger.error(f"An error occurred while validating stream url: {e}")
            return False

    def get_frame_bytes(self) -> bytes | None:
        """
        Scrapes the latest frame from a video stream URL and returns it as bytes.

        Returns:
            bytes | None: The frame encoded as a JPEG byte array, or None if unsuccessful.
        """
        _url = (
            self.get_url_with_yt_dlp(self.url)
            if "youtube.com/watch?v=" in self.url
            else self.url
        )

        try:
            ret, frame = self._read_frame(_url)
            if not ret or frame is None:
                self.logger.warning(
                    f"Failed to retrieve a frame from {self.location_name} video stream."
                )
                return None

            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                self.logger.warning("Failed to encode frame to JPEG format.")
                return None

            return buffer.tobytes()

        except Exception as e:
            self.logger.error(f"{self.location_name}: {e}")
            raise e


# Selectors tried in order when no explicit selector is provided.
# Each entry is tried against the live DOM; the first non-empty result wins.
# The largest element by pixel area is chosen when multiple matches exist.
_BROWSER_SOURCE_AUTO_SELECTORS: list[str] = ["video", "canvas", "iframe"]


class BrowserSource(Source):
    """
    Captures frames from a webcam that is embedded in a web page (e.g. inside
    an <iframe>, a <video> element loaded by JavaScript, or a canvas-based
    WebRTC player) by rendering the page in a headless Chromium browser and
    screenshotting the relevant element.

    This is useful when the underlying stream URL is token-authenticated,
    hashed, IP-locked, or otherwise not directly accessible — the browser
    handles all of that transparently.

    Attributes:
        selector: str | None - An optional CSS selector that pinpoints the
            webcam element (e.g. ``'#webcam video'``, ``'iframe.cam-embed'``).
            When *None* the class auto-detects the best candidate by trying
            ``<video>``, ``<canvas>``, and ``<iframe>`` elements in that order
            and picking the largest one by pixel area.

        persistent_session: bool - When *True* a single headless browser is
            opened on the first ``get_frame_bytes()`` call and kept alive for
            the lifetime of this object. Subsequent calls re-use the same page,
            so only one full page load is ever performed and the browser cache
            absorbs all static assets (JS, CSS, fonts). This is the more
            server-friendly mode and the one that best mimics a human who leaves
            the browser tab open all day. When *False* (default) a fresh browser
            is launched and torn down for every frame — simpler, but heavier on
            both your machine and the remote server.

            Call ``close()`` when done to release the persistent session.

        page_load_timeout_ms: int - How long (ms) to wait for the page to
            finish loading before giving up. Defaults to 30 000.

        element_timeout_ms: int - How long (ms) to wait for the target element
            to appear in the DOM after the page has loaded. Defaults to 15 000.

        blank_brightness_threshold: float - Mean pixel brightness (0–255) below
            which a captured frame is considered blank (e.g. a black video
            player that has not yet buffered). Such frames are discarded and
            ``get_frame_bytes()`` returns *None* instead of saving a useless
            black image. Defaults to 10. Set to 0 to disable blank detection.

        dismiss_selectors: list[str] - CSS selectors for overlay close/accept
            buttons (cookie banners, donation popups, GDPR notices, etc.) that
            should be clicked once after the page loads. Each selector is tried
            in order; selectors that do not match any element are silently
            skipped. In persistent-session mode the dismissals happen once when
            the browser opens (or reopens after a crash), so the overlays stay
            gone for the entire day. In ephemeral mode they are dismissed on
            every frame capture.

            Selectors may use any syntax Playwright supports, including
            text-based selectors, e.g.::

                dismiss_selectors=[
                    "button:has-text('Разреши всички')",  # cookie banner
                    "button:has-text('Затвори')",          # Patreon popup
                ]
    """

    PAGE_LOAD_TIMEOUT_MS: int = 30_000
    ELEMENT_TIMEOUT_MS: int = 15_000
    BLANK_BRIGHTNESS_THRESHOLD: float = 10.0
    # How long to wait for each dismiss selector before giving up (ms).
    DISMISS_TIMEOUT_MS: int = 3_000

    def __init__(
        self,
        location_name: str,
        url: str,
        selector: str | None = None,
        persistent_session: bool = False,
        dismiss_selectors: list[str] | None = None,
        logger: Logger | None = None,
        weather_data_on_images: bool = False,
        weather_data_provider: "WeatherStationInfo | None" = None,
        owner: str | None = None,
        skip_validation: bool = False,
    ) -> None:
        self._selector = selector
        self._persistent_session = persistent_session
        self._dismiss_selectors: list[str] = dismiss_selectors or []
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        super().__init__(
            location_name=location_name,
            url=url,
            logger=logger,
            weather_data_on_images=weather_data_on_images,
            weather_data_provider=weather_data_provider,
            owner=owner,
            skip_validation=skip_validation,
        )

    @property
    def selector(self) -> str | None:
        """The CSS selector used to locate the webcam element, or None for auto-detect."""
        return self._selector

    @selector.setter
    def selector(self, value: str) -> None:
        """Set the CSS selector used to locate the webcam element."""
        self._selector = value

    @property
    def persistent_session(self) -> bool:
        """True if a single browser session is reused across all frame captures."""
        return self._persistent_session

    @property
    def dismiss_selectors(self) -> list[str]:
        """CSS selectors for overlay buttons to click once after page load."""
        return self._dismiss_selectors

    def _dismiss_popups(self, page: Page) -> None:
        """
        Clicks every button in ``dismiss_selectors`` to close overlays.

        Each selector is attempted with a short timeout (``DISMISS_TIMEOUT_MS``).
        Selectors that do not match any visible element are silently skipped so
        a missing or already-closed popup never interrupts frame capture.
        """
        for sel in self._dismiss_selectors:
            try:
                page.click(sel, timeout=self.DISMISS_TIMEOUT_MS)
                self.logger.debug(
                    f"{self.location_name}: dismissed overlay '{sel}'."
                )
                sleep(1)
            except Exception:
                self.logger.error(f"{self.location_name}: failed to dismiss overlay '{sel}'.")
                pass

    def _ensure_page(self) -> Page:
        """
        Returns the live persistent page, opening (or reopening after a crash)
        the browser and navigating to ``self.url`` when necessary.

        Only called in persistent-session mode.
        """
        if (
            self._browser is not None
            and self._browser.is_connected()
            and self._page is not None
        ):
            return self._page

        # First open, or recovery after a browser crash / lost connection.
        if self._pw is None:
            self._pw = sync_playwright().start()

        self._browser = self._pw.chromium.launch(headless=True)
        self._page = self._browser.new_page()
        self._page.goto(
            self.url,
            timeout=self.PAGE_LOAD_TIMEOUT_MS,
            wait_until="load",
        )
        self._dismiss_popups(self._page)
        self.logger.info(
            f"{self.location_name}: persistent browser session (re)opened."
        )
        return self._page

    def close(self) -> None:
        """
        Releases the persistent browser session and all associated resources.

        No-op when ``persistent_session=False`` or when the session is already
        closed. Should be called when the source is no longer needed.
        """
        if self._browser is not None:
            self._browser.close()
            self._browser = None
            self._page = None
        if self._pw is not None:
            self._pw.stop()
            self._pw = None

    def __getstate__(self) -> dict[str, Any]:
        """
        Custom pickle serialisation: strip the live Playwright runtime objects
        before the object is pickled (e.g. by CacheManager).

        Playwright's internal asyncio event loop and async-generator hooks are
        not serialisable by pickle. The browser state is dropped here and will
        be transparently recreated by ``_ensure_page()`` the next time
        ``get_frame_bytes()`` is called after the object is restored.
        """
        state = self.__dict__.copy()
        state["_pw"] = None
        state["_browser"] = None
        state["_page"] = None
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore the instance from a pickle snapshot."""
        self.__dict__.update(state)

    def _find_element(self, page: Page) -> ElementHandle | None:
        """
        Locates the webcam element on an already-loaded page.

        If a ``selector`` was provided at construction time it is used directly
        (with a wait so transient loading states are handled gracefully).
        Otherwise the auto-detection list is tried in order and the element
        with the largest bounding-box area is returned.

        Returns *None* when no suitable element can be found.
        """
        if self._selector:
            return page.wait_for_selector(
                self._selector,
                state="visible",
                timeout=self.ELEMENT_TIMEOUT_MS,
            )

        for sel in _BROWSER_SOURCE_AUTO_SELECTORS:
            candidates = page.query_selector_all(sel)
            visible = [el for el in candidates if el.is_visible()]
            if not visible:
                continue
            return max(
                visible,
                key=lambda el: (
                    (box := el.bounding_box()) and box["width"] * box["height"] or 0
                ),
            )

        return None

    def _is_blank_frame(self, jpeg_bytes: bytes) -> bool:
        """
        Returns *True* when the frame is predominantly black.

        This catches the common case where a video player has not yet buffered
        its first frame and renders a solid black rectangle. The check decodes
        the JPEG to a greyscale image and compares the mean pixel brightness
        against ``BLANK_BRIGHTNESS_THRESHOLD``.

        Always returns *False* when the threshold is set to 0 (detection
        disabled) or when the image cannot be decoded.
        """
        if self.BLANK_BRIGHTNESS_THRESHOLD <= 0:
            return False
        import numpy as np
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False
        return float(img.mean()) < self.BLANK_BRIGHTNESS_THRESHOLD

    def _screenshot_page(self, page: Page) -> bytes | None:
        """Takes a JPEG screenshot of the webcam element on *page*."""
        element = self._find_element(page)
        if element is None:
            self.logger.warning(
                f"{self.location_name}: no webcam element found. "
                f"Try providing an explicit CSS selector."
            )
            return None
        screenshot = element.screenshot(type="jpeg", quality=90)
        if self._is_blank_frame(screenshot):
            self.logger.debug(
                f"{self.location_name}: blank frame detected, skipping."
            )
            return None
        return screenshot

    def _capture_screenshot(self, url: str) -> bytes | None:
        """
        Returns a JPEG screenshot of the webcam element.

        In ephemeral mode a fresh browser is launched, used, and closed.
        In persistent mode the existing page is reused (or reopened on crash).
        """
        if self._persistent_session:
            return self._screenshot_page(self._ensure_page())

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(
                    url,
                    timeout=self.PAGE_LOAD_TIMEOUT_MS,
                    wait_until="load",
                )
                self._dismiss_popups(page)
                return self._screenshot_page(page)
            finally:
                browser.close()

    def validate_url(self, url: str) -> bool:
        """
        Validates that the page loads and a webcam element can be found.

        Args:
            url: str - The URL of the web page containing the embedded webcam.

        Returns:
            bool: True if a suitable element is detected, otherwise False.
        """
        try:
            result = self._capture_screenshot(url)
            if result is None:
                return False
            self.logger.info(
                f"{self.location_name} has a valid browser source url for collecting images"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"An error occurred while validating browser source url: {e}"
            )
            return False

    def get_frame_bytes(self) -> bytes | None:
        """
        Returns a JPEG screenshot of the webcam element as bytes.

        In ephemeral mode (``persistent_session=False``) a headless browser is
        launched and torn down on every call. In persistent mode the existing
        page is reused — call ``close()`` when the source is no longer needed.

        Returns:
            bytes | None: JPEG-encoded screenshot, or None if unsuccessful.
        """
        try:
            return self._capture_screenshot(self.url)
        except Exception as e:
            self.logger.error(f"{self.location_name}: {e}")
            raise e

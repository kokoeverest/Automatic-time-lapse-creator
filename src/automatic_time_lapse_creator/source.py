from queue import Queue
from typing import Any
from .common.logger import configure_logger
from .common.constants import OK_STATUS_CODE
from .common.exceptions import InvalidStatusCodeException
from .weather_station_info import WeatherStationInfo
import cv2
import subprocess
import requests
from logging import Logger


class Source:
    """
    Represents a webcam source for capturing images or video frames.

    This class handles both static image webcams and video stream sources. It provides
    functionality for retrieving images, validating video streams, and managing metadata
    such as the number of collected images and video creation status.

    Attributes:
        location_name: str - The name of the location. This is used for organizing
            the images and videos into appropriate folders.

        url: str - The URL of the webcam feed (it should poit to either an image resource or a video stream).

        url_is_video_stream: bool - Indicates whether the URL points to a video stream.

        weather_data_on_images: bool - Set this to True if the images already have weather data
        on them

        weather_data_provider: WeatherStationInfo | None - An optional provider for retrieving weather data to overlay on images.
        #### *weather_data_provider will be ignored if the weather_data_on_images is set to True in order to avoid duplicate data.*

        _is_valid_url: bool - Whether the provided URL is a valid for collecting images from.
        _is_valid_stream: bool - Whether the provided URL is a valid video stream.
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
        log_queue: Queue[Any] | None = None,
        is_video_stream: bool = False,
        weather_data_on_images: bool = False,
        weather_data_provider: WeatherStationInfo | None = None,
    ) -> None:
        self.location_name = location_name
        self.url = url
        self.url_is_video_stream = is_video_stream
        self.logger = configure_logger(logger_name="Source", log_queue=log_queue)

        if self.url_is_video_stream:
            self._is_valid_url = False
            self._is_valid_stream = self.validate_stream_url(url, self.logger)
        else:
            self._is_valid_stream = False
            self._is_valid_url = self.validate_url(url, self.logger)

        self._has_weather_data = weather_data_on_images

        if self._has_weather_data and weather_data_provider is not None:
            self.logger.warning(
                "Weather data on images is set to True!\nWeather data provider will be ignored to avoid duplicate data on images!"
            )
            self.weather_data_provider = None
        else:
            self.weather_data_provider = weather_data_provider
            if not self.has_weather_data and self.weather_data_provider is not None:
                self.logger.info(f"Weather provider set for {self.location_name}")

        self._daily_video_created: bool = False
        self._monthly_video_created: bool = False
        self._images_count: int = 0
        self._all_images_collected: bool = False
        self._images_partially_collected: bool = False

    @property
    def has_weather_data(self) -> bool:
        """
        If weather data is originally available on the images for the given url.

        Returns:
            bool: True if weather data exists on images, otherwise False.
        """
        return self._has_weather_data

    @property
    def is_valid_stream(self) -> bool:
        """
        Checks whether the provided URL is a valid video stream.

        Returns:
            bool: True if the URL is a valid video stream, otherwise False.
        """
        return self._is_valid_stream

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

    @classmethod
    def validate_stream_url(cls, url: str, logger: Logger):
        """
        Validates if the given URL is a valid video stream.

        If the URL is a YouTube link, it attempts to retrieve a direct video stream URL
        using `yt-dlp`. Then, OpenCV tries to open the stream and check if frames can be read.

        Args:
            url: str - The URL of the video stream.

        Returns:
            bool: True if the URL is a valid video stream, otherwise False.
        """
        _url = cls.get_url_with_yt_dlp(url) if "youtube.com/watch?v=" in url else url

        try:
            cap = cv2.VideoCapture(_url)

            ret, _ = cap.read()
            if not ret:
                logger.warning(
                    f"Source: {_url} is not a valid url and will be ignored!"
                )
                return False

            cap.release()
            logger.info(f"{url} is a valid stream for collecting images")
            return True

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return False

    @classmethod
    def validate_url(cls, url: str, logger: Logger):
        """Verifies the provided url will return bytes content.

        Returns::
            bool - if the response returns bytes content.
        """

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except Exception as exc:
            logger.error(f"Something went wrong during check of url {url}! Maybe it points to a video stream?\n({exc})")
            return False
        if isinstance(response.content, bytes):
            logger.info(f"{url} is a valid source for collecting images")
            return True
        else:
            logger.warning(f"{url} is NOT a valid source for collecting images")
            return False

    @classmethod
    def get_url_with_yt_dlp(cls, url: str):
        """Use yt-dlp to extract the direct URL"""

        command = ["yt-dlp", "-g", "--format", "best", url]
        result = subprocess.run(command, capture_output=True, text=True)
        video_url = result.stdout.strip()
        return video_url

    def get_frame_bytes(self) -> bytes | None:
        """
        Fetches the bytes content of the url's response depending on the type of webcam url.
        It will not try to fetch an image if the url is marked as invalid!

            Returns::
                bytes | None - if the result was successful or not
        """
        if not self.url_is_video_stream and self.is_valid_url:
            return self.fetch_image_from_static_web_cam()

        if self.url_is_video_stream and self.is_valid_stream:
            return self.fetch_image_from_stream()

    def fetch_image_from_stream(self) -> bytes | None:
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
            cap = cv2.VideoCapture(_url)

            ret, frame = cap.read()
            if not ret:
                self.logger.warning(
                    f"Failed to retrieve a frame from {self.location_name} video stream."
                )
                return None

            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                self.logger.warning("Failed to encode frame to JPEG format.")
                return None

            cap.release()
            return buffer.tobytes()

        except Exception as e:
            self.logger.error(f"{self.location_name}: {e}")
            raise e

    def fetch_image_from_static_web_cam(self) -> bytes | Any:
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

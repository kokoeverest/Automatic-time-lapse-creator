from typing import Any
from .weather_station_info import WeatherStationInfo
import cv2
import subprocess
import requests
import logging

logger = logging.getLogger("Source")


class Source:
    """Contains two public attributes and four read-only attributes, which can be changed
    through the respective methods.

    Attributes::

        location_name: str - a folder with that name will be created on your pc. The videos
            for every day of the execution of the TimeLapseCreator will be created and put into
            subfolders into the "location_name" folder

        url: str - a valid web address where a webcam frame (image) should be located.


    """

    def __init__(
        self,
        location_name: str,
        url: str,
        is_video_stream: bool = False,
        weather_data_on_images: bool = False,
        weather_data_provider: WeatherStationInfo | None = None,
    ) -> None:
        self.location_name = location_name
        self.url = url
        self.url_is_video_stream = is_video_stream

        if self.url_is_video_stream:
            self._is_valid_stream = self.validate_stream_url(url)
        else:
            self._is_valid_stream = False

        self._has_weather_data = weather_data_on_images
        if self._has_weather_data and weather_data_provider is not None:
            logger.warning(
                "Weather data on images is set to True!\nWeather data provider will be ignored to avoid duplicate data on images!"
            )
            self.weather_data_provider = None
        else:
            logger.info(f"Weather provider set for {self.location_name}")
            self.weather_data_provider = weather_data_provider

        self._video_created: bool = False
        self._images_count: int = 0
        self._all_images_collected: bool = False
        self._images_partially_collected: bool = False

    @property
    def has_weather_data(self) -> bool:
        return self.weather_data_provider is not None

    @property
    def is_valid_stream(self) -> bool:
        return self._is_valid_stream

    @property
    def images_collected(self) -> bool:
        return self._all_images_collected

    @property
    def images_partially_collected(self) -> bool:
        return self._images_partially_collected

    @property
    def images_count(self) -> int:
        return self._images_count

    @property
    def video_created(self) -> bool:
        return self._video_created

    def set_video_created(self) -> None:
        """Set the video_created to True"""
        self._video_created = True

    def reset_video_created(self) -> None:
        """Reset the video_created to False"""
        self._video_created = False

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
    def validate_stream_url(cls, url: str):
        """
        Scrapes the latest frame from a video stream URL and returns bool of the operation success.

        Args:
            video_url: str - URL of the video stream.

        Returns:
            bool: True if successful, False otherwise.
        """
        _url = cls.get_url_with_yt_dlp(url) if "youtube.com/watch?v=" in url else url

        try:
            cap = cv2.VideoCapture(_url)

            ret, _ = cap.read()
            if not ret:
                logger.warning(f"Source: {url} is not a valid url and will be ignored!")
                return False

            cap.release()
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
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
        Fetches the bytes content of the url's response depending on the type of webcam url

            Returns::
                bytes | None - if the result was successful or not
        """
        if not self.url_is_video_stream:
            return self.fetch_image_from_static_web_cam()

        if self.url_is_video_stream and self.is_valid_stream:
            return self.fetch_image_from_stream()

    def fetch_image_from_stream(self) -> bytes | None:
        """
        Scrapes the latest frame from a video stream URL and returns it as bytes.

        Returns:
            bytes | None: The frame encoded as a JPEG byte array, or None if unsuccessful.
        """
        _url = self.get_url_with_yt_dlp(self.url)
        try:
            cap = cv2.VideoCapture(_url)

            ret, frame = cap.read()
            if not ret:
                logger.warning(
                    f"Failed to retrieve a frame from {self.location_name} video stream."
                )
                return None

            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                logger.warning("Failed to encode frame to JPEG format.")
                return None

            cap.release()
            # logger.info(f"{self.location_name} fetched image from video stream")
            return buffer.tobytes()

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def fetch_image_from_static_web_cam(self) -> bytes | Any:
        """Verifies the request status code is 200.

        Raises::

            InvalidStatusCodeException if the code is different,
            because request.content would not be accessible and the program will crash.

        Returns::
            bytes | Any - the content of the response if Exception is not raised."""

        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except Exception as exc:
            logger.error(exc, exc_info=True)
            raise exc
        # logger.info(f"{self.location_name} fetched image from static webcam")
        return response.content

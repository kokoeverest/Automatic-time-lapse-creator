from __future__ import annotations
from logging import Logger
import logging.handlers
import logging
import os
import requests
from datetime import datetime as dt, timezone as tz
from time import sleep
from pathlib import Path
from typing import Any, Iterable
from .cache_manager import CacheManager
from .source import Source
from .video_manager import (
    VideoManager as vm,
)
from .time_manager import (
    LocationAndTimeManager,
)
from .common.constants import (
    YYMMDD_FORMAT,
    HHMMSS_COLON_FORMAT,
    HHMMSS_UNDERSCORE_FORMAT,
    LOG_FILE,
    JPG_FILE,
    MP4_FILE,
    LOG_INTERVAL,
    LOGS_DIR,
    LOGGING_FORMAT,
    OK_STATUS_CODE,
    DEFAULT_PATH_STRING,
    DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_VIDEO_WIDTH,
)
from .common.exceptions import (
    InvalidStatusCodeException,
    InvalidCollectionException,
)
from .common.utils import create_log_message


logger: Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
cwd = os.getcwd()
Path(f"{cwd}{LOGS_DIR}").mkdir(exist_ok=True)
filename = Path(f"{cwd}{LOGS_DIR}/{dt.now().strftime(YYMMDD_FORMAT)}{LOG_FILE}")
date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=filename, when=LOG_INTERVAL, utc=True
)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(fmt=LOGGING_FORMAT, datefmt=date_fmt)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class TimeLapseCreator:
    """
    For convenience the TimeLapseCreator can be instantiated with all iterable collections, except for dict().
    Internally the self.sources is manipulated as a set, ensuring that there will be no duplicate sources added by mistake.
    #### Note: for testing purposes the while loop in execute() is set to break when the self._test_counter == 0.
    #### You should not set the nighttime_retry_seconds to 1 when instantiating a new TimeLapseCreator because
    #### it will stop after the first iteration
    """

    def __init__(
        self,
        sources: Iterable[Source] = [],
        city: str = DEFAULT_CITY_NAME,
        path: str = DEFAULT_PATH_STRING,
        seconds_between_frames: int = DEFAULT_SECONDS_BETWEEN_FRAMES,
        night_time_retry_seconds: int = DEFAULT_NIGHTTIME_RETRY_SECONDS,
        video_fps: int = DEFAULT_VIDEO_FPS,
        video_width: int = DEFAULT_VIDEO_WIDTH,
        video_height: int = DEFAULT_VIDEO_HEIGHT,
    ) -> None:
        self.base_path = os.path.join(os.getcwd(), path)
        self.folder_name = dt.today().strftime(YYMMDD_FORMAT)
        self.location = LocationAndTimeManager(city)
        self.sources: set[Source] = TimeLapseCreator.validate_collection(sources)
        self.wait_before_next_frame = seconds_between_frames
        self.nighttime_wait_before_next_retry = night_time_retry_seconds
        self.video_fps = video_fps
        self.video_width = video_width
        self.video_height = video_height
        self._test_counter = night_time_retry_seconds

    def get_cached_self(self) -> TimeLapseCreator:
        """Retrieve the state of the object from the cache. If the retrieved TimeLapseCreator is older
        than one day, then its state will be ignored and a default state will be used.
        If object of other type than TimeLapseCreator is returned (including Exception) it will be ignored
        and the current object will be returned (self).

        Returns::
            TimeLapseCretor - either the cached object state or the current state"""
        try:
            old_object = CacheManager.get(
                location=self.location.city.name, path_prefix=self.base_path
            )
            if (
                isinstance(old_object, TimeLapseCreator)
                and old_object.folder_name == self.folder_name
            ):
                return old_object
            else:
                return self
        except Exception:
            return self

    def cache_self(self) -> None:
        """Writes the current state of the TimeLapseCreator to the cache."""
        CacheManager.write(
            self, location=self.location.city.name, path_prefix=self.base_path
        )

    def execute(self) -> None:
        """Verifies that self.sources has at least one Source and starts a while loop. Then, according to the return
        of collect_images_from_webcams():
          ##### - creates the video for every source
          ##### - waits the nighttime retry time interval.
        If the source.all_images_collected is True the sources' images are deleted after the video is created.
        If the source.images_partially_collected, the sources' images won't be deleted.

        Returns::
            None
        """
        self = self.get_cached_self()
        self.verify_sources_not_empty()

        # self._test_counter > 0 for testing purposes only, see Note in TimeLapseCreator docstring
        while self._test_counter > 0:
            self.reset_test_counter()
            collected = self.collect_images_from_webcams()
            if collected or (
                not collected
                and any(source.images_partially_collected for source in self.sources)
                and any(not source.video_created for source in self.sources)
            ):
                for source in self.sources:
                    # the normal flow of images collection, when all images are collected during the day
                    if (
                        dt.now(tz.utc) > self.location.end_of_daylight
                        and source.images_collected
                        and not source.images_partially_collected
                        and not source.video_created
                    ):
                        if self.create_video(source):
                            source.set_video_created()
                    # if there was an interruption in program's execution but some images were collected
                    # create a video anyway, but don't delete the source images
                    elif (
                        dt.now(tz.utc) > self.location.end_of_daylight
                        and source.images_partially_collected
                        and not source.images_collected
                        and not source.video_created
                    ):
                        if self.create_video(source, delete_source_images=False):
                            source.set_video_created()
            else:
                sleep(self.nighttime_wait_before_next_retry)

            self._decrease_test_counter()

    def collect_images_from_webcams(self) -> bool:
        """While self.location.is_daylight() returns True, the images for every source
        will be extracted from the url. If self.location.is_daylight() returns False
        the logger will log 'Not daylight yet' and the return will be False.

        Returns::

            True - when images are collected during the daylight interval

            False - if it's not daylight yet.
        """
        if self.location.is_daylight():
            self.reset_all_sources_counters_to_default_values()
            logger.info(
                f"Start collecting images @{self.location.city.name}\n    Sunrise: {self.location.start_of_daylight}\n    Sunset: {self.location.end_of_daylight}"
            )

            while self.location.is_daylight():
                for source in self.sources:
                    try:
                        img = self.verify_request(source)

                        file_name = dt.now().strftime(HHMMSS_UNDERSCORE_FORMAT)
                        current_path = f"{self.base_path}/{source.location_name}/{self.folder_name}"

                        Path(current_path).mkdir(parents=True, exist_ok=True)
                        if img:
                            full_path = Path(f"{current_path}/{file_name}{JPG_FILE}")

                            with open(full_path, "wb") as file:
                                file.write(img)
                            source.increase_images()
                            source.set_images_partially_collected()
                            self.cache_self()

                    except Exception as e:
                        logger.error(e)
                        continue
                sleep(self.wait_before_next_frame)

            self.set_sources_all_images_collected()
            self.cache_self()
            logger.info(f"Finished collecting for {self.folder_name}")
            return True
        else:
            logger.info(f"Not daylight yet @{self.location.city.name}")
            self.is_it_next_day()
            return False

    def is_it_next_day(self) -> None:
        old_date = dt.strptime(self.folder_name, YYMMDD_FORMAT)
        new_date = dt.today()

        if (
            new_date.year > old_date.year
            or new_date.month > old_date.month
            or new_date.day > old_date.day
        ):
            self.folder_name = new_date.strftime(YYMMDD_FORMAT)
            logger.info(
                f"New day starts!\nSunrise: {self.location.start_of_daylight}; Sunset: {self.location.end_of_daylight}"
            )

    def create_video(self, source: Source, delete_source_images: bool = True) -> bool:
        """Creates a video from the source collected images. If delete_source_images is True
        the source image files will be deleted after the video is created

        Attributes::

            source: Source - the source from which collected images the video will be created

            delete_source_images: bool - if the source images should be deleted as well"""

        input_folder = str(
            Path(f"{self.base_path}/{source.location_name}/{self.folder_name}")
        )
        output_video = str(Path(f"{input_folder}/{self.folder_name}{MP4_FILE}"))

        created = False
        if not vm.video_exists(output_video):
            created = vm.create_timelapse(
                input_folder,
                output_video,
                self.video_fps,
                self.video_width,
                self.video_height,
            )
            # else:
            #   created = True

        if created and delete_source_images:
            _ = vm.delete_source_images(input_folder)

        return created

    def verify_sources_not_empty(self) -> None:
        """Verifies that TimeLapseCreator has at least one Source to take images for.

        Raises::

            ValueError if there are no sources added."""

        if len(self.sources) == 0:
            raise ValueError("You should add at least one source for this location!")

    def verify_request(self, source: Source) -> bytes | Any:
        """Verifies the request status code is 200.

        Raises::

            InvalidStatusCodeException if the code is different,
            because request.content would not be accessible and the program will crash.

        Returns::
            bytes | Any - the content of the response if Exception is not raised."""

        try:
            response = requests.get(source.url)
            if response.status_code != OK_STATUS_CODE:
                raise InvalidStatusCodeException(
                    f"Status code {response.status_code} is not {OK_STATUS_CODE} for url {source}"
                )
        except Exception as exc:
            raise exc

        return response.content

    def reset_images_partially_collected(self) -> None:
        """Resets the images_partially_collected = False for all self.sources"""
        [source.reset_images_partially_collected() for source in self.sources]

    def reset_all_sources_counters_to_default_values(self) -> None:
        """Resets the images_count = 0, resets video_created = False, resets
        images_collected = False and resets reset_images_pertially_collected = False
        for all self.sources
        """
        for source in self.sources:
            source.reset_images_counter()
            source.reset_video_created()
            source.reset_all_images_collected()
            source.reset_images_partially_collected()

    def set_sources_all_images_collected(self) -> None:
        """Sets -> images_collected = True for all self.sources
        and calls self.reset_images_partially_collected(), because all images are collected
        """
        [source.set_all_images_collected() for source in self.sources]
        self.reset_images_partially_collected()

    def add_sources(self, sources: Source | Iterable[Source]) -> None:
        """Adds a single Source or a collection[Source] to the TimeLapseCreator sources.
        If any source to be added already exists (location_name or url) a warning will be logged
        and the source will not be added.

        Raises::

            InvalidCollectionException if the passed collection is a dictionary."""

        try:
            sources = TimeLapseCreator.check_sources(sources)

            if isinstance(sources, Source):
                if self.source_exists(sources):
                    logger.warning(
                        create_log_message(sources.location_name, sources.url, "add")
                    )
                else:
                    self.sources.add(sources)

            elif not isinstance(sources, Source):
                for source in sources:
                    if self.source_exists(source):
                        logger.warning(
                            create_log_message(source.location_name, source.url, "add")
                        )
                    else:
                        self.sources.add(source)
        except InvalidCollectionException as exc:
            raise exc

    def source_exists(self, source: Source) -> bool:
        """Checks if any source in self.sources has a match in the location_name or the url.

        Returns::
            bool - True if a match is found, False if no match is found."""
        return any(
            source.location_name == existing.location_name or source.url == existing.url
            for existing in self.sources
        )

    def remove_sources(self, sources: Source | Iterable[Source]) -> None:
        """Removes a single Source or a collection[Source] from the TimeLapseCreator sources.
        If any source to be removed is not found (location_name or url) a warning will be logged.

        Raises::

            InvalidCollectionException if the passed collection is a dictionary."""

        try:
            sources = TimeLapseCreator.check_sources(sources)
            if isinstance(sources, Source):
                if not self.source_exists(sources):
                    logger.warning(
                        create_log_message(sources.location_name, sources.url, "remove")
                    )
                else:
                    self.sources.remove(sources)
            else:
                for source in sources:
                    if not self.source_exists(source):
                        logger.warning(
                            create_log_message(
                                source.location_name, source.url, "remove"
                            )
                        )
                    else:
                        self.sources.remove(source)

        except InvalidCollectionException as exc:
            raise exc
        except Exception as exc:
            logger.exception(exc)

    @classmethod
    def check_sources(cls, sources: Source | Iterable[Source]) -> Source | set[Source]:
        """Checks if a single source or a collection of sources is passed.
        Parameters::

            sources: Source | Iterable[Source]

        Returns::

            Source | set[Source] if the containing collection is of type set, list or tuple.

        Raises::

            InvalidCollectionException if the collection is passed as dictionary."""

        if isinstance(sources, Source):
            return sources

        return cls.validate_collection(sources)

    @classmethod
    def validate_collection(cls, sources: Iterable[Source]) -> set[Source]:
        """Checks if a valid collection is passed.
        Parameters::

            sources: Iterable[Source]

        Returns::

            set[Source] if the containing collection is of type set, list or tuple.

        Raises::

            InvalidCollectionException if the collection is passed as dictionary."""
        allowed_collections = (set, list, tuple)

        if any(isinstance(sources, col) for col in allowed_collections):
            return set(sources)
        else:
            raise InvalidCollectionException(
                "Only list, tuple or set collections are allowed!"
            )

    def _decrease_test_counter(self) -> None:
        """Decreases the test counter by 1."""
        self._test_counter -= 1

    def reset_test_counter(self) -> None:
        """
        Resets the self._test_couter to equal self.nighttime_wait_before_next_retry.

        You should use this method only when testing, in order to meet the breaking condition in
        the while loop in the execute() method.
        """
        self._test_counter = self.nighttime_wait_before_next_retry

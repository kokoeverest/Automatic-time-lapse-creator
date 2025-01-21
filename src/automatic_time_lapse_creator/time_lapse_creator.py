from __future__ import annotations
import os
import requests
from datetime import datetime as dt, timezone as tz, timedelta as td
from time import sleep
from pathlib import Path
from queue import Queue
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
    HHMMSS_UNDERSCORE_FORMAT,
    JPG_FILE,
    MP4_FILE,
    OK_STATUS_CODE,
    DEFAULT_PATH_STRING,
    DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_DAY_FOR_MONTHLY_VIDEO,
    VideoType,
)
from .common.exceptions import (
    InvalidStatusCodeException,
    InvalidCollectionException,
)
from glob import glob
from .common.utils import (
    create_log_message,
    shorten,
    dash_sep_strings,
    video_type_response,
)
from . import configure_logger


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
        quiet_mode: bool = True,
        log_queue: Queue[Any] | None = None,
    ) -> None:
        """Quiet_mode is set to True by default which will suppress the log messages on every call
        to self.location.is_daylight() during the night and also on every image taken during the day.
        Switching it to True will generate a lot of log messages!
        """
        self.base_path = os.path.join(os.getcwd(), path)
        self.folder_name = dt.today().strftime(YYMMDD_FORMAT)

        self.logger = configure_logger(
            log_queue=log_queue, logger_base_path=self.base_path
        )

        self.location = LocationAndTimeManager(city, self.logger)
        self.sources: set[Source] = self.validate_collection(sources)
        self.wait_before_next_frame = seconds_between_frames
        self.nighttime_wait_before_next_retry = night_time_retry_seconds
        self.video_fps = video_fps
        self.video_width = video_width
        self.video_height = video_height
        self.quiet_mode = quiet_mode
        self.video_queue = None
        self.log_queue = log_queue
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
                location=self.location.city.name,
                path_prefix=self.base_path,
                logger=self.logger,
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
            time_lapse_creator=self,
            location=self.location.city.name,
            path_prefix=self.base_path,
            quiet=self.quiet_mode,
            logger=self.logger,
        )

    def clear_cache(self):
        CacheManager.clear_cache(
            location=self.location.city.name,
            path_prefix=self.base_path,
            logger=self.logger,
        )

    def execute(
        self,
        video_queue: Queue[Any] | None = None,
        log_queue: Queue[Any] | None = None,
    ) -> None:
        """Verifies that self.sources has at least one Source and starts a while loop. Then, according to the return
        of collect_images_from_webcams():
          ##### - creates the video for every source
          ##### - waits the nighttime retry time interval.
        If the source.all_images_collected is True the sources' images are deleted after the video is created.
        If the source.images_partially_collected, the sources' images won't be deleted.

        Returns::
            None
        """
        self.video_queue = video_queue
        if log_queue:
            self.log_queue = log_queue
            _, tail = os.path.split(self.base_path)
            self.logger = configure_logger(log_queue, tail)
        try:
            self.logger.info("Program starts!")
            self = self.get_cached_self()
            self.verify_sources_not_empty()

            # self._test_counter > 0 for testing purposes only, see Note in TimeLapseCreator docstring
            while self._test_counter > 0:
                self.reset_test_counter()
                collected = self.collect_images_from_webcams()
                if collected or (
                    not collected
                    and any(
                        source.images_partially_collected for source in self.sources
                    )
                    and any(not source.video_created for source in self.sources)
                ):
                    for source in self.sources:
                        video_path = str(
                            Path(
                                f"{self.base_path}/{source.location_name}/{self.folder_name}"
                            )
                        )
                        # the normal flow of images collection, when all images are collected during the day
                        if (
                            dt.now(tz.utc) > self.location.end_of_daylight
                            and source.images_collected
                            and not source.images_partially_collected
                            and not source.video_created
                        ):
                            if self.create_video(source):
                                source.set_video_created()
                                if self.video_queue is not None:
                                    self.video_queue.put(
                                        video_type_response(
                                            video_path, VideoType.DAILY.value
                                        )
                                    )
                                self.cache_self()
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
                                if self.video_queue is not None:
                                    self.video_queue.put(
                                        video_type_response(
                                            video_path, VideoType.DAILY.value
                                        )
                                    )
                                self.cache_self()
                else:
                    # monthly summary logic
                    if self.is_next_month():
                        self.process_monthly_summary()
                    sleep(self.nighttime_wait_before_next_retry)

                self._decrease_test_counter()
        except KeyboardInterrupt:
            self.logger.info("Program execution cancelled...")

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
            self.logger.info(f"Start collecting images @{self.location.city.name}")

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
                        self.logger.error(e)
                        continue
                sleep(self.wait_before_next_frame)

            self.set_sources_all_images_collected()
            self.cache_self()
            self.logger.info(f"Finished collecting for {self.folder_name}")
            return True
        else:
            if not self.quiet_mode:
                self.logger.info(f"Not daylight yet @{self.location.city.name}")
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
            self.logger.info(
                f"New day starts!\nSunrise: {self.location.start_of_daylight} UTC; Sunset: {self.location.end_of_daylight} UTC"
            )

    def create_video(self, source: Source, delete_source_images: bool = True) -> bool:
        """Creates a video from the source collected images. If delete_source_images is True
        the source image files will be deleted after the video is created

        Args::

            source: Source - the source from which collected images the video will be created

            delete_source_images: bool - if the source images should be deleted as well"""

        input_folder = str(
            Path(f"{self.base_path}/{source.location_name}/{self.folder_name}")
        )
        output_video = str(Path(f"{input_folder}/{self.folder_name}{MP4_FILE}"))

        created = False
        if not vm.video_exists(output_video):
            self.logger.info(f"Video doesn't exist in {shorten(input_folder)}")
            created = vm.create_timelapse(
                self.logger,
                input_folder,
                output_video,
                self.video_fps,
                self.video_width,
                self.video_height,
            )
            # else:
            #   created = True

        if created and delete_source_images:
            _ = vm.delete_source_media_files(self.logger, input_folder)

        return created

    def verify_sources_not_empty(self) -> None:
        """Verifies that TimeLapseCreator has at least one Source to take images for.

        Raises::

            ValueError if there are no sources added."""

        if len(self.sources) == 0:
            raise ValueError("You should add at least one source for this location!")

    def verify_request(self, source: Source, retry: bool = False) -> bytes | Any:
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
            if not retry:
                sleep(3)
                self.logger.info(f"Retrying request for {source.location_name}")
                self.verify_request(source, retry=True)
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
                    self.logger.warning(
                        create_log_message(sources.location_name, sources.url, "add")
                    )
                else:
                    self.sources.add(sources)

            elif not isinstance(sources, Source):
                for source in sources:
                    if self.source_exists(source):
                        self.logger.warning(
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
                    self.logger.warning(
                        create_log_message(sources.location_name, sources.url, "remove")
                    )
                else:
                    self.sources.remove(sources)
            else:
                for source in sources:
                    if not self.source_exists(source):
                        self.logger.warning(
                            create_log_message(
                                source.location_name, source.url, "remove"
                            )
                        )
                    else:
                        self.sources.remove(source)

        except InvalidCollectionException as exc:
            raise exc
        except Exception as exc:
            self.logger.exception(exc)

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

    def valid_folder(self, *args: str):
        """
        Validates a folder based on the provided arguments.

        This method checks whether a specified folder exists and if its name starts with a given prefix
        based on the year and month.

        Args:
            *args (str): A sequence of strings representing:
                - base: The base directory path.
                - folder_name: The name of the folder to validate.
                - year: The year used to validate the folder's name.
                - month: The month used to validate the folder's name.

        Returns:
            str | None: Returns the folder name if it exists and matches the criteria; otherwise, None.
        """
        base, folder_name, year, month = args
        if not os.path.isdir(os.path.join(base, folder_name)):
            return
        if not folder_name.startswith(dash_sep_strings(year, month)):
            return

        return folder_name

    def get_video_files_paths(self, base_folder: str, year: str, month: str):
        """
        Retrieves video file paths for a specific year and month from a base folder.

        This method scans the base folder for subfolders that match the specified year and month,
        validates them, and collects the paths of video files matching the expected naming pattern.

        Args:
            base_folder: str - The base directory to search for video files.
            year: str - The year used to validate subfolder names and video file prefixes.
            month: str - The month used to validate subfolder names and video file prefixes.

        Returns:
            list[str]: A list of file paths to the video files found in valid subfolders.
        """
        folders = os.listdir(base_folder)
        video_files_paths: list[str] = []
        for folder in folders:
            if self.valid_folder(base_folder, folder, year, month):
                video_file = glob(
                    os.path.join(
                        base_folder,
                        folder,
                        f"{dash_sep_strings(year, month)}*{MP4_FILE}",
                    )
                )
                if len(video_file) > 0 and video_file[0] != "":
                    video_files_paths.append(next(iter(video_file)))

        return video_files_paths

    def create_monthly_video(
        self,
        base_path: str,
        year: str,
        month: str,
        delete_source_files: bool = False,
        extension: str = MP4_FILE,
    ):
        """
        Creates a monthly summary video by combining video files from a specific year and month.

        This method identifies all video files for the given year and month in the specified base path,
        combines them into a single output video, and optionally deletes the source video files after
        successful creation.

        Args:
            base_path: str - The base directory containing the subfolders with video files.
            year: str - The year to filter subfolders and video files.
            month: str - The month to filter subfolders and video files.
            delete_source_files: bool - If True, deletes the source video files and their parent
                folders after the summary video is created. Defaults to False.
            extension: str - The file extension of the video files to process. Defaults to MP4_FILE.

        Returns:
            str | None: Returns the path to the folder containing the created monthly summary video if
                successful, otherwise None.
        """
        yy_mm_format = dash_sep_strings(year, month)

        video_files = self.get_video_files_paths(
            base_folder=base_path, year=year, month=month
        )
        video_folder_name = os.path.join(base_path, yy_mm_format)
        output_video_name = os.path.join(
            video_folder_name, f"{yy_mm_format}{extension}"
        )

        if len(video_files) == 0:
            self.logger.warning(
                f"No folders found for a monthly summary video - {shorten(output_video_name)}!"
            )
            return

        if vm.create_monthly_summary_video(
            self.logger,
            video_files,
            output_video_name,
            DEFAULT_VIDEO_FPS,
            DEFAULT_VIDEO_WIDTH,
            DEFAULT_VIDEO_HEIGHT,
        ):
            self.logger.info(f"Video created: {shorten(output_video_name)}")

            if delete_source_files:
                for video_path in video_files:
                    head, _ = os.path.split(video_path)
                    vm.delete_source_media_files(
                        logger=self.logger,
                        path=head,
                        extension=extension,
                        delete_folder=True,
                    )

            return video_folder_name

    def is_next_month(
        self,
    ) -> bool:
        """
        Checks if it is the right time for creating a monthly summary video.

            Returns::

                bool
        """
        if dt.today().day == DEFAULT_DAY_FOR_MONTHLY_VIDEO and 2 < dt.now().hour < 6:
            return True
        if not self.quiet_mode:
            self.logger.info("Not next month")
        return False

    def process_monthly_summary(self):
        """Create and optionally send the monthly summary video to the queue."""
        year, month = self.get_previous_year_and_month()

        for source in self.sources:
            base_path = os.path.join(self.base_path, source.location_name)
            new_video = self.create_monthly_video(base_path, year, month)

            if new_video and self.video_queue:
                self.video_queue.put(
                    video_type_response(new_video, VideoType.MONTHLY.value)
                )
        self.logger.info(f"Monthly summaries created for {year}-{month}")

    def get_previous_year_and_month(self):
        """
        Gets the previous year and month at the time of calling

            Returns::

                tuple[str] - containing the year and month
        """
        datetime_object = dt.strptime(self.folder_name, YYMMDD_FORMAT)
        days_offset = td(days=DEFAULT_DAY_FOR_MONTHLY_VIDEO + 1)
        prev_date = datetime_object - days_offset

        return (str(prev_date.year), str(prev_date.month))

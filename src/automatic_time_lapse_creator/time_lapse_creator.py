from __future__ import annotations
import os
from datetime import datetime as dt, timedelta as td
from time import sleep
from pathlib import Path
from queue import Queue
from typing import Any, Iterable, NamedTuple
from glob import glob
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
    HHMMSS_COLON_FORMAT,
    JPG_FILE,
    MP4_FILE,
    DEFAULT_PATH_STRING,
    DEFAULT_CITY_NAME,
    DEFAULT_NIGHTTIME_RETRY_SECONDS,
    DEFAULT_SECONDS_BETWEEN_FRAMES,
    DEFAULT_VIDEO_FPS,
    VIDEO_HEIGHT_360p,
    VIDEO_WIDTH_360p,
    DEFAULT_DAY_FOR_MONTHLY_VIDEO,
    DEFAULT_SUNRISE_OFFSET,
    DEFAULT_SUNSET_OFFSET,
    LOG_START_INT,
    VideoType,
)
from .common.exceptions import (
    InvalidCollectionException,
)
from .common.utils import (
    create_log_message,
    shorten,
    dash_sep_strings,
    video_type_response,
)
from .common.logger import configure_root_logger
from .text_box import TextBox, TopOutsideTextBox


class TimeLapseCreator:
    """
    The TimeLapseCreator is responsible for managing the collection of images from various sources
    and generating time-lapse videos on a daily and monthly basis.

    This class ensures that all sources are managed as a set to prevent duplicate entries.
    It provides flexibility in configuring various parameters, such as capture intervals,
    video resolution, logging behavior, and monthly summary settings.

    **Note:**
    - For testing purposes, the while loop in `execute()` is set to break when `self._test_counter == 0`.
    - The `night_time_retry_seconds` parameter should not be set to 1 when instantiating a new TimeLapseCreator,
      as it will cause execution to stop after the first iteration.
    - The `quiet_mode` parameter is set to `True` by default to suppress excessive logging. If set to `False`,
      log messages will be generated for every call to `self.location.is_daylight()` during the night and
      for every image taken during the day.

    Attributes:
        sources: set[Source] - A collection of unique sources from which images will be captured.
        city: str - The name of the city used for daylight calculations.
        base_path: str - The root directory where time-lapse images and videos are stored.
        folder_name: str - The name of the current day's folder for image storage.
        wait_before_next_frame: int - Interval in seconds between consecutive image captures.
        nighttime_wait_before_next_retry: int - Interval in seconds between retries during nighttime.
        video_fps: int - Frames per second for the generated videos.
        video_width: int - Width of the output videos in pixels.
        video_height: int - Height of the output videos in pixels.
        sunrise_offset_minutes: int - Minutes to offset the calculated sunrise time.
        sunset_offset_minutes: int - Minutes to offset the calculated sunset time.
        text_box_position: type[box.TextBox] | None - the class for positioning of the text box containing 
        the image's time of day and weather data text, defaults to TopOutsideTextBox
        text_box_transparency: float - the transparency of the text box (only if it's inside the image), defaults to box.TextBox.TRANSPARENCY_MID,
        quiet_mode: bool - Whether to suppress frequent log messages.
        create_monthly_summary_video: bool - Whether to generate a monthly summary video.
        day_for_monthly_summary_video: int - The day of the month when the summary video should be created.
        delete_daily_videos_after_monthly_summary_is_created: bool - Whether to delete daily videos after the monthly summary is generated.
        log_queue: Queue[Any] | None - A queue for handling log messages across processes.
        video_queue: Queue[Any] | None - A queue for managing video creation and upload tasks.
        location: LocationAndTimeManager - Handles daylight calculations and time-based operations.
        logger: Logger - Logger instance for handling logging.
    """

    def __init__(
        self,
        sources: Iterable[Source] = [],
        city: str = DEFAULT_CITY_NAME,
        path: str = DEFAULT_PATH_STRING,
        seconds_between_frames: int = DEFAULT_SECONDS_BETWEEN_FRAMES,
        night_time_retry_seconds: int = DEFAULT_NIGHTTIME_RETRY_SECONDS,
        video_fps: int = DEFAULT_VIDEO_FPS,
        video_width: int = VIDEO_WIDTH_360p,
        video_height: int = VIDEO_HEIGHT_360p,
        sunrise_offset_minutes: int = DEFAULT_SUNRISE_OFFSET,
        sunset_offset_minutes: int = DEFAULT_SUNSET_OFFSET,
        text_box_position: type[TextBox] | None = TopOutsideTextBox,
        text_box_transparency: float = TextBox.TRANSPARENCY_MID,
        create_monthly_summary_video: bool = True,
        day_for_monthly_summary_video: int = DEFAULT_DAY_FOR_MONTHLY_VIDEO,
        delete_daily_videos_after_monthly_summary_is_created: bool = True,
        quiet_mode: bool = True,
        log_queue: Queue[Any] | None = None,
    ) -> None:
        self.base_path = os.path.join(os.getcwd(), path)
        self.folder_name = dt.today().strftime(YYMMDD_FORMAT)

        self.logger = configure_root_logger(
            log_queue=log_queue, logger_base_path=self.base_path
        )

        self.location = LocationAndTimeManager(
            city_name=city,
            sunrise_offset=self._validate("sunrise_offset_minutes", sunrise_offset_minutes),
            sunset_offset=self._validate("sunset_offset_minutes", sunset_offset_minutes),
            logger=self.logger,
        )
        self.sources: set[Source] = self.validate_collection(sources)
        self.wait_before_next_frame = self._validate("seconds_between_frames", seconds_between_frames)
        self.nighttime_wait_before_next_retry = self._validate("night_time_retry_seconds", night_time_retry_seconds)
        self.video_fps = self._validate("video_fps", video_fps)
        self.video_width = self._validate("video_width", video_width)
        self.video_height = self._validate("video_height", video_height)
        self.text_box_position = text_box_position
        self.text_box_transparency = text_box_transparency
        self.quiet_mode = quiet_mode
        self.video_queue = None
        self.log_queue = log_queue
        self._monthly_summary = create_monthly_summary_video
        self._day_for_monthly_summary = day_for_monthly_summary_video
        self._delete_daily_videos = delete_daily_videos_after_monthly_summary_is_created
        self._test_counter = night_time_retry_seconds

    def _validate(self, attr_name: str, attr_value: int):
        """
        Validates the attribute value based on predefined rules.

        This method checks if the provided attribute value is of the correct type and within the allowed range.
        If the value is not of the correct type, a TypeError is raised. If the value is out of range, a warning
        is logged, and the attribute value is set to its default value.

        Args:
            attr_name: str - The name of the attribute to validate.
            attr_value: int - The value of the attribute to validate.

        Returns:
            int - The validated attribute value, either the original value if valid or the default value if out of range.

        Raises:
            TypeError: If the attribute value is not of the expected type.
        """
        Attr = NamedTuple("Attr", [("type", type), ("range", range), ("default", int)])

        attrs: dict[str, Attr] = {
            "sunrise_offset_minutes" : Attr(int, range(1, 301), DEFAULT_SUNRISE_OFFSET),
            "sunset_offset_minutes" : Attr(int, range(1, 301), DEFAULT_SUNSET_OFFSET),
            "seconds_between_frames" : Attr(int, range(1, 601), DEFAULT_SECONDS_BETWEEN_FRAMES),
            "night_time_retry_seconds" : Attr(int, range(1, 601), DEFAULT_NIGHTTIME_RETRY_SECONDS),
            "video_fps" : Attr(int, range(1, 61), DEFAULT_VIDEO_FPS),
            "video_width" : Attr(int, range(640, 1921), VIDEO_WIDTH_360p),
            "video_height" : Attr(int, range(360, 1081), VIDEO_HEIGHT_360p),
        }

        if not isinstance(attr_value, attrs[attr_name].type):
            raise TypeError(f"{attr_name} must be of type {attrs[attr_name].type}")
        
        if attr_value not in attrs[attr_name].range:
            self.logger.warning(f"{attr_name} must be in {attrs[attr_name].range}! Setting to default: {attrs[attr_name].default}")
            attr_value = attrs[attr_name].default
        
        return attr_value

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
        """Deletes the cache file for the current TimeLapseCreator"""
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
        """
        Executes the main time-lapse creation process for the configured sources.

        This method verifies that `self.sources` contains at least one valid source and initiates a continuous
        while loop. Within the loop, the following steps are performed:

        1. Calls `collect_images_from_webcams()` to gather images from sources.
        2. Depending on the result of image collection:
           - If all images are successfully collected for a source:
             - Creates a video from the collected images.
             - Deletes the source's images after video creation.
             - Sends the video information to the `video_queue` if provided.
           - If images are partially collected (e.g., due to an interruption):
             - Creates a video from the partially collected images without deleting them.
             - Sends the video information to the `video_queue` if provided.

        3. If it's the start of a new month, initiates the monthly summary video creation process by calling
           `process_monthly_summary()`.

        4. If no conditions are met, the program waits for the configured nighttime retry interval before retrying.

        The method logs key events and maintains a cache of the current state to ensure continuity in case of
        interruptions.

        Parameters:
            video_queue: Queue[Any] | None - A queue to send video information for further processing or uploading.
            log_queue: Queue[Any] | None - A queue for centralized logging across processes.

        Returns:
            None
        """

        self.video_queue = video_queue
        if log_queue:
            self.log_queue = log_queue
            _, tail = os.path.split(self.base_path)
            self.logger = configure_root_logger(log_queue, tail)
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
                    and any(not source.daily_video_created for source in self.sources)
                ):
                    for source in self.sources:
                        video_path = str(
                            Path(
                                f"{self.base_path}/{source.location_name}/{self.folder_name}"
                            )
                        )
                        if (
                            self.location.time_now > self.location.end_of_daylight
                            and source.images_collected
                            and not source.images_partially_collected
                            and not source.daily_video_created
                        ):
                            if self.create_video(source):
                                source.set_daily_video_created()
                                if self.video_queue is not None:
                                    self.video_queue.put(
                                        video_type_response(
                                            video_path, VideoType.DAILY.value
                                        )
                                    )
                                self.cache_self()
                        elif (
                            self.location.time_now > self.location.end_of_daylight
                            and source.images_partially_collected
                            and not source.images_collected
                            and not source.daily_video_created
                        ):
                            if self.create_video(source, delete_source_images=False):
                                source.set_daily_video_created()
                                if self.video_queue is not None:
                                    self.video_queue.put(
                                        video_type_response(
                                            video_path, VideoType.DAILY.value
                                        )
                                    )
                                self.cache_self()
                else:
                    if self._monthly_summary:
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
                        img = source.get_frame_bytes()

                        if img:
                            if source.weather_data_provider:
                                source.weather_data_provider.get_data()

                            file_name = self.location.time_now.strftime(HHMMSS_UNDERSCORE_FORMAT)
                            current_path = f"{self.base_path}/{source.location_name}/{self.folder_name}"
                            dt_text = f"{self.folder_name} {self.location.time_now.strftime(HHMMSS_COLON_FORMAT)}"

                            Path(current_path).mkdir(parents=True, exist_ok=True)
                            full_path = Path(f"{current_path}/{file_name}{JPG_FILE}")

                            vm.save_image_with_weather_overlay(
                                image_bytes=img,
                                save_path=str(full_path),
                                width=self.video_width,
                                height=self.video_height,
                                date_time_text=dt_text,
                                weather_data_text=str(source.weather_data_provider)
                                if source.weather_data_provider
                                else None,
                                text_box_position=self.text_box_position,
                                text_box_transparency=self.text_box_transparency
                            )

                            source.increase_images()
                            source.set_images_partially_collected()
                            self.cache_self()

                    except Exception:
                        continue
                sleep(self.wait_before_next_frame)

            self.set_sources_all_images_collected()
            self.cache_self()
            self.logger.info(f"Finished collecting for {self.folder_name}")
            return True
        else:
            if not self.quiet_mode:
                self.logger.info(f"Not daylight yet @{self.location.city.name} {self.location.time_now.strftime(HHMMSS_COLON_FORMAT)}")
            self.is_it_next_day()
            return False

    def is_it_next_day(self) -> None:
        """Checks if the next day have started and changes the self.folder_name accordingly"""
        old_date = dt.strptime(self.folder_name, YYMMDD_FORMAT)
        new_date = self.location.time_now

        if (
            new_date.year > old_date.year
            or new_date.month > old_date.month
            or new_date.day > old_date.day
        ):
            self.folder_name = new_date.strftime(YYMMDD_FORMAT)
            self.logger.info(
                f"New day starts! Images will be collected between:\n"
                f"{LOG_START_INT * ' '}Start time: {self.location.start_of_daylight.strftime(HHMMSS_COLON_FORMAT)}  -->"
                f"  End time: {self.location.end_of_daylight.strftime(HHMMSS_COLON_FORMAT)}"
            )

    def create_video(self, source: Source, delete_source_images: bool = True) -> bool:
        """
        Creates a video from the source collected images. If delete_source_images is True
        the source image files will be deleted after the video is created.

        Args::

            source: Source - the source's collected images from which the video will be created

            delete_source_images: bool - if the source images should be deleted as well
        """
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
            )
        else:
            created = True

        if created and delete_source_images:
            _ = vm.delete_source_media_files(self.logger, input_folder)

        return created

    def verify_sources_not_empty(self) -> None:
        """Verifies that TimeLapseCreator has at least one Source to take images for.

        Raises::

            ValueError if there are no sources added."""

        if len(self.sources) == 0:
            raise ValueError("You should add at least one source for this location!")

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
            source.reset_daily_video_created()
            source.reset_monthly_video_created()
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

    @staticmethod
    def valid_folder(*args: str):
        """
        Validates a folder based on the provided arguments.

        This method checks whether a specified folder exists and if its name starts with a given prefix
        based on the year and month.

        Args:
            *args: str - A sequence of strings representing:
                - base: The base directory path.
                - folder_name: The name of the folder to validate.
                - year: The year used to validate the folder's name.
                - month: The month used to validate the folder's name.

        Returns:
            bool - Returns True if the folder exists and matches the criteria; otherwise, False.
        """
        base, folder_name, year, month = args
        if not os.path.isdir(os.path.join(base, folder_name)):
            return False
        if not folder_name.startswith(dash_sep_strings(year, month)):
            return False

        return True

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
            list[str] - A list of file paths to the video files found in valid subfolders.
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
            str | None - Returns the path to the folder containing the created monthly summary video if
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
            logger=self.logger,
            video_paths=video_files,
            output_video_path=output_video_name,
            fps=DEFAULT_VIDEO_FPS,
        ):
            self.logger.info(f"Video created: {shorten(output_video_name)}")

            if self._delete_daily_videos:
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
        if dt.today().day == self._day_for_monthly_summary and 2 < dt.now().hour < 6:
            return True
        if not self.quiet_mode:
            self.logger.info("Not next month")
        return False

    def process_monthly_summary(self):
        """Create and optionally send the monthly summary video to the queue."""
        year, month = self.get_previous_year_and_month()

        for source in self.sources:
            base_path = os.path.join(self.base_path, source.location_name)

            if not source.monthly_video_created:
                new_video = self.create_monthly_video(base_path, year, month)

                if new_video:
                    source.set_monthly_video_created()
                    self.logger.info(
                        f"Monthly summary created for {source.location_name}, {year}-{month}"
                    )

                    if self.video_queue:
                        self.video_queue.put(
                            video_type_response(new_video, VideoType.MONTHLY.value)
                        )

    def get_previous_year_and_month(self):
        """
        Gets the previous year and month at the time of calling

            Returns::

                tuple[str] - containing the year and month
        """
        datetime_object = dt.strptime(self.folder_name, YYMMDD_FORMAT)
        days_offset = td(days=DEFAULT_DAY_FOR_MONTHLY_VIDEO + 1)
        prev_date = datetime_object - days_offset
        if prev_date.month < 10:
            month = "0" + str(prev_date.month)
        else:
            month = str(prev_date.month)

        return (str(prev_date.year), month)

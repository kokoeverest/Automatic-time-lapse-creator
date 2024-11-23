import os
import requests
from datetime import datetime as dt
from time import sleep
from pathlib import Path
from typing import Iterable
import logging
from src.automatic_time_lapse_creator_kokoeverest.source import Source
from src.automatic_time_lapse_creator_kokoeverest.video_manager import (
    VideoManager as vm,
)
from src.automatic_time_lapse_creator_kokoeverest.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator_kokoeverest.common.constants import (
    YYMMDD_FORMAT,
    HHMMSS_COLON_FORMAT,
    HHMMSS_UNDERSCORE_FORMAT,
    LOG_FILE,
    JPG_FILE,
    OK_STATUS_CODE,
    MP4_FILE,
)
from src.automatic_time_lapse_creator_kokoeverest.common.exceptions import (
    InvalidStatusCodeException,
    InvalidCollectionException,
)

cwd = os.getcwd()
Path(f"{cwd}/logs").mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=Path(f"{cwd}/logs/{dt.now().strftime(YYMMDD_FORMAT)}{LOG_FILE}"),
    level=logging.INFO,
    format="%(name)s: %(asctime)s - %(levelname)s - %(message)s",
    datefmt=f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(name)s: %(asctime)s - %(levelname)s - %(message)s")

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class TimeLapseCreator:
    """"""

    def __init__(
        self,
        sources: list[Source] = [],
        city: str = "Sofia",
        path: str = os.getcwd(),
        seconds_between_frames: int = 60,
        night_time_retry_seconds: int = 300,
        video_fps: int = 30,
        video_width: int = 640,
        video_height: int = 360,
    ) -> None:
        self.base_path = path
        self.folder_name = dt.today().strftime(YYMMDD_FORMAT)
        self.location = LocationAndTimeManager(city)
        self.sources: set[Source] = set(sources)
        self.wait_before_next_frame = seconds_between_frames
        self.nighttime_wait_before_next_retry = night_time_retry_seconds
        self.video_fps = video_fps
        self.video_width = video_width
        self.video_height = video_height

    def execute(self):
        """If the source.all_images_collected is True
        Don't delete the source images if there's a
        problem with the output video"""

        self.verify_sources_not_empty()
        while True:
            # images_collected, images_partially_collected = (
            self.collect_images_from_webcams()
            # )

            for source in self.sources:
                # the normal flow of images collection, when all images are collected during the day
                if (
                    dt.now() > self.location.end_of_daylight
                    and source.images_collected
                    and not source.images_partially_collected
                    and not source.video_created
                ):
                    self.create_video(source)
                # if there was an interruption in program's execution but some images were collected
                # create a video anyway, but don't delete the source images
                elif (
                    dt.now() > self.location.end_of_daylight
                    and source.images_partially_collected
                    and not source.images_collected
                    and not source.video_created
                ):
                    self.create_video(source, delete_source_images=False)
            else:
                sleep(self.nighttime_wait_before_next_retry)

    def collect_images_from_webcams(self) -> None:
        """"""
        # images_collected, images_partially_collected = False, False

        if self.location.is_daylight():
            self.reset_all_sources_counters_to_default_values()
            logger.info("Start collecting images")

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

                    except Exception as e:
                        logger.error(e)
                        continue
                sleep(self.wait_before_next_frame)

            self.set_sources_all_images_collected()
            # self.reset_images_partially_collected()
            # images_collected, images_partially_collected = True, False
            logger.info(f"Finished collecting for today")

            # return images_collected, images_partially_collected
        else:
            logger.info("Not daylight yet")

        # return images_collected, images_partially_collected

    def create_video(self, source: Source, delete_source_images: bool = True):
        """Creates a video from the source collected images. If delete_source_images is True
        the source image files will be deleted after the video is created

        Attributes::

            source: Source - the source from which collected images the video will be created

            delete_source_images: bool - if the source images should be deleted as well"""

        # for source in self.sources:
        input_folder = f"{self.base_path}/{source.location_name}/{self.folder_name}"
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
        if created:
            source.set_video_created()

        if source.video_created and delete_source_images:
            _ = vm.delete_source_images(input_folder)

    def verify_sources_not_empty(self):
        """Verifies that TimeLapseCreator has at least one Source to take images for.

        Raises::

            ValueError if there are no sources added."""

        if len(self.sources) == 0:
            raise ValueError("You should add at least one source for this location!")

    def verify_request(self, source: Source):
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

    def reset_images_partially_collected(self):
        """Resets the images_partially_collected = False for all self.sources"""
        for source in self.sources:
            source.reset_images_pertially_collected()

    def reset_all_sources_counters_to_default_values(self):
        """Resets the images_count = 0, resets video_created = False and
        resets images_collected = False for all self.sources
        """
        for source in self.sources:
            source.reset_images_counter()
            source.reset_video_created()
            source.reset_all_images_collected()
            source.reset_images_pertially_collected()

    def set_sources_all_images_collected(self):
        """Sets -> images_collected = True for all self.sources
        and calls self.reset_images_partially_collected(), because all images are collected
        """
        for source in self.sources:
            source.set_all_images_collected()
        self.reset_images_partially_collected()

    def add_sources(self, sources: Source | Iterable[Source]):
        """Adds a single Source or a collection[Source] to the TimeLapseCreator sources.

        Raises::

            InvalidCollectionException if the passed collection is a dictionary."""

        try:
            sources = self._check_sources(sources)
        except InvalidCollectionException as exc:
            raise exc

        if isinstance(sources, Source):
            self.sources.add(sources)
        else:
            self.sources.update(set(sources))

    def remove_sources(self, sources: Source | Iterable[Source]):
        """Removes a single Source or a collection[Source] from the TimeLapseCreator sources.

        Raises::

            InvalidCollectionException if the passed collection is a dictionary."""

        try:
            sources = self._check_sources(sources)
        except InvalidCollectionException as exc:
            raise exc

        if isinstance(sources, Source):
            self.sources.remove(sources)
        else:
            for src in sources:
                self.sources.remove(src)

    def _check_sources(self, sources: Source | Iterable[Source]):
        """Checks if the sources are in a valid container.
        Parameters::

            sources: Source | Iterable[Source]

        Returns::

            Source | set[Source] if the containing collection is of type set, list or tuple.

        Raises::

            InvalidCollectionException if the collection is passed as dictionary."""

        allowed_collections = (set, list, tuple)

        if isinstance(sources, Source):
            return sources

        if any(isinstance(sources, col) for col in allowed_collections):
            return set(sources)
        else:
            raise InvalidCollectionException(
                "Only list, tuple or set collections are allowed!"
            )

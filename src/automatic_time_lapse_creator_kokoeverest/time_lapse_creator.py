import os
import requests
from datetime import datetime as dt
from time import sleep
from typing import NamedTuple
from pathlib import Path
from typing import Iterable
import logging
from src.automatic_time_lapse_creator_kokoeverest.video_manager import (
    VideoManager as vm,
)
from src.automatic_time_lapse_creator_kokoeverest.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator_kokoeverest.common.constants import (
    JPG_FILE,
    MP4_FILE,
    LOG_FILE,
    YYMMDD_FORMAT,
    HHMMSS_UNDERSCORE_FORMAT,
    HHMMSS_COLON_FORMAT,
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
    level=logging.DEBUG,
    format="%(name)s: %(asctime)s - %(levelname)s - %(message)s",
    datefmt=f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(name)s: %(asctime)s - %(levelname)s - %(message)s")

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class Source(NamedTuple):
    """The Source class contains two attributes:

    Attributes::

        location_name: str - a folder with that name will be created on your pc. The videos
            for every day of the execution of the TimeLapseCreator will be created and put into
            subfolders into the "location_name" folder

        url: str - a valid web address where a webcam frame (image) should be located.
    Be sure that the url does not point to a video resource."""

    location_name: str
    url: str


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
        self.wait_before_next_retry = night_time_retry_seconds
        self.video_fps = video_fps
        self.video_width = video_width
        self.video_height = video_height

    def execute(self):
        """"""

        self.verify_sources_not_empty()
        while True:
            images_collected = self.collect_images_from_webcams()

            if dt.now() > self.location.end_of_daylight and images_collected:
                for source in self.sources:
                    input_folder = (
                        f"{self.base_path}/{source.location_name}/{self.folder_name}"
                    )
                    output_video = str(
                        Path(f"{input_folder}/{self.folder_name}{MP4_FILE}")
                    )

                    if not vm.video_exists(output_video):
                        created = vm.create_timelapse(
                            input_folder,
                            output_video,
                            self.video_fps,
                            self.video_width,
                            self.video_height,
                        )
                    else:
                        created = False

                    if created:
                        _ = vm.delete_source_images(input_folder)
            else:
                logger.info("Not daylight yet")
                sleep(self.wait_before_next_retry)

    def collect_images_from_webcams(self) -> bool:
        """"""

        if self.location.is_daylight():
            logger.info("Start collecting images")

            while self.location.is_daylight():
                for source in self.sources:
                    try:
                        img = self.verify_request(source)

                        location = source.location_name
                        file_name = dt.now().strftime(HHMMSS_UNDERSCORE_FORMAT)
                        current_path = f"{self.base_path}/{location}/{self.folder_name}"

                        Path(current_path).mkdir(parents=True, exist_ok=True)
                        if img:
                            full_path = Path(f"{current_path}/{file_name}{JPG_FILE}")

                            with open(full_path, "wb") as file:
                                file.write(img)
                    except Exception as e:
                        logger.error(e)
                        continue
                sleep(self.wait_before_next_frame)

            logger.info(f"Finished collecting for today")
            return True

        return False

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
            if response.status_code != 200:
                raise InvalidStatusCodeException(
                    f"Status code {response.status_code} is not 200 for url {source}"
                )
        except Exception as exc:
            raise exc

        return response.content

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

import os
import requests
from datetime import datetime as dt
from time import sleep
from typing import NamedTuple
from pathlib import Path
from src.automatic_time_lapse_creator_kokoeverest.video_manager import VideoManager as vm
from src.automatic_time_lapse_creator_kokoeverest.time_manager import (
    LocationAndTimeManager,
)
from src.automatic_time_lapse_creator_kokoeverest.common.constants import (
    JPG_FILE,
    MP4_FILE,
    YYMMDD_FORMAT,
    HHMMSS_FORMAT,
)
from src.automatic_time_lapse_creator_kokoeverest.common.exceptions import InvalidStatusCodeException


class Source(NamedTuple):
    location_name: str
    url: str
    """The Source class contains two parameters:

    :location_name : str - a folder with that name will be created on your pc. The videos
    for every day of the execution of the TimeLapseCreator will be created and put into
    subfolders into the "location_name" folder.

    :url : str - a valid web address where a webcam frame (image) should be located.
    Be sure that the url does not point to a video resource."""


class TimeLapseCreator:
    """"""

    def __init__(
        self,
        sources: list[Source],
        city: str = "Sofia",
        seconds_between_frames: int = 60,
        night_time_retry_seconds: int = 300,
    ) -> None:
        self.base_path = os.getcwd()
        self.folder_name = dt.today().strftime(YYMMDD_FORMAT)
        self.location = LocationAndTimeManager(city)
        self.sources: set[Source] = set(sources)
        self.wait_before_next_frame = seconds_between_frames
        self.wait_before_next_retry = night_time_retry_seconds

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
                    output_video = str(Path(f"{input_folder}/{self.folder_name}{MP4_FILE}"))

                    if not vm.video_exists(output_video):
                        created = vm.create_timelapse(input_folder, output_video)
                    else:
                        created = False

                    if created:
                        _ = vm.delete_source_images(input_folder)
            else:
                print(f"Not daylight yet: {dt.now()}")
                sleep(self.wait_before_next_retry)

    def collect_images_from_webcams(self):
        """"""

        if self.location.is_daylight():
            print(f"Start collecting images: {dt.now()}")

            while self.location.is_daylight():
                for source in self.sources:
                    try:
                        img = self.verify_request(source)

                        location = source.location_name
                        file_name = dt.now().strftime(HHMMSS_FORMAT)
                        current_path = f"{self.base_path}/{location}/{self.folder_name}"

                        Path(current_path).mkdir(parents=True, exist_ok=True)
                        if img:
                            full_path = Path(f"{current_path}/{file_name}{JPG_FILE}")
                            
                            with open(full_path, "wb") as file:
                                file.write(img)
                    except Exception as e:
                        print(str(e))
                        continue
                sleep(self.wait_before_next_frame)

            print(f"Finished collecting for today: {dt.now()}")
            return True

        return False

    def verify_sources_not_empty(self):
        """Verifies that TimeLapseCreator has at least one Source to take images for.

        Raises ValueError if there are no sources added."""

        if len(self.sources) == 0:
            raise ValueError("You should add at least one source for this location!")

    def verify_request(self, source: Source):
        """Verifies the request status code is 200.

        Raises InvalidStatusCodeException if the code is different,
        because request.content would not be accessible and the program will crash.

        Returns the content of the response if Exception is not raised."""

        try:
            response = requests.get(source.url)
            print(f"Status code is: {response.status_code}")
            if response.status_code != 200:
                raise InvalidStatusCodeException(
                    f"Status code {response.status_code} is not 200 for url {source}"
            )
        except Exception as exc:
            raise exc
        
        return response.content

    def add_sources(self, sources: Source | set[Source]):
        """Adds a single Source or a collection[Source] to the TimeLapseCreator sources."""

        if isinstance(sources, Source):
            self.sources.add(sources)
        else:
            self.sources.update(set(sources))

    def remove_sources(self, sources: Source | set[Source]):
        """Removes a single Source or a collection[Source] from the TimeLapseCreator sources."""

        if isinstance(sources, Source):
            self.sources.remove(sources)
        else:
            for src in sources:
                self.sources.remove(src) 

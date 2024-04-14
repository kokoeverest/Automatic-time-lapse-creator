import os
import requests
from datetime import datetime as dt
from time import sleep
from collections import namedtuple
from pathlib import Path
from app.video_manager import VideoManager as vm
from app.time_manager import LocationAndTimeManager


class Source(namedtuple("Source", ["location_name", "url"])):
    """The Source class contains two parameters:

    :location_name - a folder with that name will be created on your pc. The videos
    for every day of the execution of the TimeLapseCreator will be created and put into
    subfolders into the "location_name" folder.

    :url - a valid web address where a webcam frame (image) should be located.
    Be sure that the url does not point to a video resource."""

    __slots__ = ()


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
        self.folder_name = dt.today().strftime("%Y-%m-%d")
        self.location = LocationAndTimeManager(city)
        self.sources = set(sources)
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
                    output_video = f"{input_folder}/{self.folder_name}.mp4"

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
                        file_name = dt.now().strftime("%H:%M:%S")
                        current_path = f"{self.base_path}/{location}/{self.folder_name}"

                        Path(current_path).mkdir(parents=True, exist_ok=True)
                        if img:
                            with open(f"{current_path}/{file_name}.jpg", "wb") as file:
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
        
        if not self.sources:
            raise ValueError("You should add at least one source for this location!")

    def verify_request(self, source: Source):
        """Verifies the request status code is 200.
        
        Raises Exception if the code is different, 
        beacause request.content would not be accessible and the program will crash."""

        response = requests.get(source.url)
        if response.status_code != 200:
            raise Exception(f"Status code {response.status_code} is not 200 for url {source}")

        return response.content
        
    def add_sources(self, sources: Source):
        """Accepts a single Source or a collection[Source]."""

        if isinstance(sources, Source):
            self.sources.add(sources)
        else:
            self.sources.update(set(sources))

    def remove_source(self, source: Source):
        """Accepts a single Source or a collection[Source]."""

        if isinstance(source, Source):
            self.sources.remove(source)
        else:
            (self.sources.remove(src) for src in source)
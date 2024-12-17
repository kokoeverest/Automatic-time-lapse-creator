# Automatic time lapse creator

> ### A Python package for extracting images from a web cam url and converting these images into a timelapse. The process is intended to be automatic, so the only parameters that need to be provided are:
> - the image resourse url/urls pointing to an image *(not video!)*
> - the path on your computer where the images will be stored *(default is os.getcwd())*
> - the location of the city (or coordinates) for which the daylight will be calculated *(default is Sofia, Bulgaria)*

### The purpose of the program is to get an archive/history of the weather in any place that has accessible web cam, so people can actually see what the real weather was like in this place and compare it with weather forecast and/or data from a weather station.

> ### Libraries used in the program:
> - Astral (https://astral.readthedocs.io/en/latest/) - to get the 
sunrise and sunset time of the day for a specific geolocation
> - OpenCV-Python (https://pypi.org/project/opencv-python/) - to 
read/resize the jpeg files and build a time lapse mp4 video
> - Requests - builtin module used to retrieve the image from the url
> - Logging - the builtin python looging tool for creating comprehensive 
logs of the program execution
> - Pytest, unittest.mock - testing and mocking objects in isolation

> ### Main flow and automation:
> When the execution of the TimeLapseCreator object starts, it will check if it's daylight at the provided location. Daylight is calculated automatically using the Astral library so there will be few or no images collected during the night. After the collection of images finishes for the day the VideoManager creates a video from the collected images for each of the provided sources and deletes all the images for the day. In case of an interruption of the collection of images during the day (for example: power outage - the program stops and then it's started again), the video will still be created but the daily images won't be deleted. In this case you can inspect them and create a video manually from the pictures that are worth it.
> During the night the program will not collect any images - they will be collected when there is daylight - the smart power of the Astral library ;)

> ### Known issues
> - Images are randomly saved into folders: [#5](https://github.com/kokoeverest/Automatic-time-lapse-creator/issues/5) "Cache doesn't work as expected"

> ### A valid scenario for creating a TimeLapseCreator for webcams in Bulgaria:
> ***Note that no location is provided in the examples, so the TimeLapseCreator will be instantiated for the default location: Sofia, Bulgaria.***
```python
from automatic_time_lapse_creator.time_lapse_creator import TimeLapseCreator
from automatic_time_lapse_creator.source import Source

# Valid sources
borovets_source = Source(
    "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
)
pleven_hut_source = Source(
    "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)

sources_list: list[Source] = [borovets_source, pleven_hut_source]

# creating a TimeLapseCreator can be done in two ways:
# instantiate the creator directly with the list of Sources
bulgaria_webcams = TimeLapseCreator(sources_list)

# or create a new TimeLapseCreator and add the list of Sources
# with the add_sources method
bulgaria_webcams = TimeLapseCreator()
bulgaria_webcams.add_sources(sources_list)

# if you try to instantiate a new TimeLapseCreator with a single Source, it will raise an InvalidCollectionException
# for example:
pleven_hut_webcam = TimeLapseCreator(pleven_hut_source)
# output:
Traceback...:
...in validate_collection
    raise InvalidCollectionException(
src.automatic_time_lapse_creator.common.exceptions.InvalidCollectionException: Only list, tuple or set collections are allowed!

# start the collection of the images with the execute() method
bulgaria_webcams.execute()
```

> An invalid scenario will be:
```python
# Invalid source
sample_source_with_empty_url = Source("fake", "https://empty.url")

invalid_source_list = [sample_source_with_empty_url]

invalid_url_creator = TimeLapseCreator(invalid_source_list)

invalid_url_creator.execute()
```

> Should you have any questions, bug reports or recommendations, feel free to open an issue on
 the [Issues page](https://github.com/kokoeverest/Automatic-time-lapse-creator/issues)
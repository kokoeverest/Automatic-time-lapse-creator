# Automatic Time Lapse Creator

### A Python package for extracting images from a web cam url and converting these images into a timelapse. The process is intended to be automatic, so the only parameters that need to be provided are:
- the resourse url/urls pointing to an image or a valid video stream 
- the path on your computer where the images will be stored *(default is os.getcwd())*
- the location of the city for which the daylight will be calculated *(default is Sofia, Bulgaria)*

### The purpose of the program is to get an archive/history of the weather in any place that has accessible web cam, so people can actually see what the real weather was like in this place and compare it with weather forecast and/or data from a weather station.

> ### 🚨 Breaking Changes in Version 2.0.0
> - Refactored Source Class
> - Source is now an abstract base class (ABC).
> - Two new concrete classes inherit from it:
> - ImageSource(Source): Handles static images retrieved from a URL.
> - StreamSource(Source): Handles video streams and extracts frames.
> #### This change ensures better separation of concerns and explicit handling of different webcam types.
> - Improved Time Calculations
> - LocationAndTimeManager now considers the geolocation time zone when calculating sunrise and sunset times.
> - This makes the daylight calculation more accurate for locations with daylight saving time adjustments.
> #### New YouTubeChannelManager
> - Introduced YouTubeChannelManager for managing a YouTube channel's videos.
> - Enables users to list uploaded videos and delete failed uploads directly via API calls.

### Libraries used in the program:
**Automatic Time Lapse Creator is created in strict type checking mode in Visual Studio Code.**
- Astral (https://astral.readthedocs.io/en/latest/) - to get the 
sunrise and sunset time of the day for a specific geolocation
- OpenCV-Python (https://pypi.org/project/opencv-python/) - to 
read/resize the jpeg files and build a time lapse mp4 video
- Requests - the module used to retrieve the image from the url of the webcam
- Pytest, unittest.mock - testing and mocking objects in isolation
- yt-dlp - for getting the correct video stream url from a live youtube stream
- Playwright (https://playwright.dev/python/) - headless Chromium browser used by `BrowserSource` to capture frames from webcams embedded in web pages (iframes, JavaScript video players, WebRTC streams, etc.)
- google data api v3 - for uploading the videos to a youtube channel (optional)

### Installation
The latest release is available for installation via pip:
```pip install automatic-time-lapse-creator```

The latest releases under development are available on the TestPyPi web page:
[TestPyPi/automatic-time-lapse-creator](https://test.pypi.org/project/automatic-time-lapse-creator/#history)
and can be installed via pip:
```pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple automatic-time-lapse-creator=='the_version_you_want'```

#### Additional setup for `BrowserSource`
`BrowserSource` requires a one-time download of the headless Chromium browser (done once per machine, not on every run):
```
playwright install chromium
```

### Main flow and automation:
- The execute() method is sufficient for images collection during the day, creating a video from them and storing the video on the file system.
- If a video_queue is provided to the execute() method the video path will be put into the queue so it can be processed in another way.
- When the execution of the TimeLapseCreator object starts, it will check if it's daylight at the provided location. 
- Daylight is calculated automatically using the Astral library so there will be few or no images collected during the night. 
- After the collection of images finishes for the day the VideoManager creates a video from the collected images for each of the provided sources and deletes all the images for the day. In case of an interruption of the collection of images during the day (for example: power outage - the program stops and then it's started again), the video will still be created but the daily images won't be deleted. In this case you can inspect them and create a video manually from the pictures that are worth it.
- During the night the program will not collect any images - they will be collected when there is daylight - the smart power of the Astral library ;)
- In the beginning of a new month by default a monthly summary video will be created from all the videos from the previous month. Optionally the source
videos and folders may not be deleted (they will be deleted by default!).

> ### 🚨 Known issues
> - If you live in a location which is far North or South and you want to collect images during the night, the maximum sunrise and sunset offsets will make the program behave differently than expected **during the longest days of the year**.
You can set the sunrise and sunset offsets to a calculated value that is smaller than the maximum allowed in order to avoid this issue. In case you have any questions, please ask on the issues page.
> - Images are randomly saved into folders: [#5](https://github.com/kokoeverest/Automatic-time-lapse-creator/issues/5) "Cache doesn't work as expected"
> - For other problems reported, please explore the issues page and check if your problem is already described there.

### 🛠️ Examples:
### A valid scenario for creating a TimeLapseCreator for webcams in Bulgaria:
> ***Note that no location is provided in the examples, so the TimeLapseCreator will be instantiated for the default location: Sofia, Bulgaria.***
```python
from automatic_time_lapse_creator.time_lapse_creator import TimeLapseCreator
from automatic_time_lapse_creator.source import ImageSource, StreamSource, Source

# Valid sources
borovets_source = ImageSource(
    location_name="markudjik", 
    url="https://media.borovets-bg.com/cams/channel?channel=31"
)
pleven_hut_source = ImageSource(
    location_name="pleven_hut", 
    url="https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)
rila_lakes_hut = StreamSource(
    location_name="rila_lakes_hut",
    url="https://home-solutions.bg/cams/rilski-ezera2.jpg?1738245934609",
)

sources_list: list[Source] = [borovets_source, pleven_hut_source, rila_lakes_hut]

# creating a TimeLapseCreator can be done in two ways:
# instantiate the creator directly with the list of Sources
bulgaria_webcams = TimeLapseCreator(sources=sources_list)

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

### 🚨 An invalid scenario will be:
```python
# Invalid source
sample_source_with_empty_url = ImageSource("fake", "https://empty.url")

invalid_source_list = [sample_source_with_empty_url]

invalid_url_creator = TimeLapseCreator(invalid_source_list)

invalid_url_creator.execute()
```

### 🌐 Using `BrowserSource` for embedded / protected webcams

Some webcams are not accessible via a direct image or stream URL — their feed is embedded inside a web page using an `<iframe>`, a JavaScript video player, a WebRTC stream, or a canvas-based renderer. The underlying stream URL is often token-authenticated, hashed, or IP-locked and cannot be used directly.

`BrowserSource` solves this by running a headless Chromium browser, loading the full web page, and screenshotting the webcam element. It works transparently regardless of how the stream is protected.

> **One-time setup required:** run `playwright install chromium` once on each machine before using `BrowserSource`.

#### Auto-detecting the webcam element

When no CSS selector is provided, `BrowserSource` automatically searches for `<video>`, `<canvas>`, and `<iframe>` elements in that order. Among all visible candidates of the same type it picks the one with the **largest pixel area**, which reliably selects the main camera feed over thumbnails or decorative elements.

```python
from automatic_time_lapse_creator.source import BrowserSource

# BrowserSource will auto-detect the largest visible video/canvas/iframe on the page
earthcam_source = BrowserSource(
    location_name="times_square",
    url="https://www.earthcam.com/usa/newyork/timessquare/",
)
```

#### Pinning a specific element with a CSS selector

If the page contains multiple video elements or the auto-detection picks the wrong one, provide an explicit CSS selector:

```python
roundshot_source = BrowserSource(
    location_name="zurich_roundshot",
    url="https://www.roundshot.com/some-live-view-page",
    selector="#webcam-player video",
)
```

#### Persistent session (server-friendly mode)

By default `BrowserSource` launches a fresh browser for every frame capture. This is the simplest mode but causes the full page (JS, CSS, fonts, analytics) to be re-downloaded each time.

Setting `persistent_session=True` opens the browser **once** and keeps the tab alive for the lifetime of the source object. Subsequent frame captures only take a screenshot of the already-loaded page — no extra network requests. This closely mimics a human who leaves the browser tab open all day and just glances at it periodically, and is the recommended mode for sites that have rate limiting or bot-detection.

```python
# Open once, screenshot repeatedly — server-friendly
earthcam_source = BrowserSource(
    location_name="times_square",
    url="https://www.earthcam.com/usa/newyork/timessquare/",
    selector="#video-player video",
    persistent_session=True,
)

bulgaria_webcams = TimeLapseCreator(sources=[earthcam_source])
bulgaria_webcams.execute()

# Release the browser when done
earthcam_source.close()
```

If the browser crashes mid-session, `BrowserSource` automatically reopens it and reloads the page on the next `get_frame_bytes()` call — no manual intervention needed.

> **Tip:** `close()` is always safe to call regardless of mode or whether the session was ever opened, so you can call it unconditionally in cleanup code.
### 📺 Managing YouTube Channel Videos

With the new YouTubeChannelManager, users can list videos and delete failed uploads:

```python
from automatic_time_lapse_creator.youtube_manager import YouTubeChannelManager, YouTubeAuth

youtube_auth = YouTubeAuth(CREDENTIALS_FILE_PATH)

youtube = YouTubeChannelManager(youtube_auth)

last_videos = youtube.list_channel()

if last_videos is not None:
    pending_videos = youtube.filter_pending_videos(last_videos)
else:
    pending_videos = []

print(f"There are {len(pending_videos)} videos with status 'uploaded'")

for video in pending_videos:
    print(f"Deleteing video {video['title']} with id: {video['id']}")
    youtube.delete_video(video["id"])
```

### 📢 Need Help?

Should you have any questions, bug reports or recommendations, feel free to open an issue on
the [Issues page](https://github.com/kokoeverest/Automatic-time-lapse-creator/issues)
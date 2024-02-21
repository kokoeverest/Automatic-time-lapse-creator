# Automatic time lapse creator

### A Python script for extracting images from a web cam url and converting these images into a timelapse. The process is intended to be automatic, so the only parameters that need to be changed are:

+ the image resourse url/urls 
+ the path on your computer where the images will be stored 
+ the location of the city (or coordinates) so the daylight will be calculated

### The purpose of the program is to get an archive/history of the weather in any place that has accessible web cam, so one can actually see what the real weather was like in this place and compare it with weather forecast and/or data from a weather station

### Libraries used in the program:
+ Astral (https://astral.readthedocs.io/en/latest/) - to get the 
sunrise and sunset time of the day for a specific geolocation
+ OpenCV-Python (https://pypi.org/project/opencv-python/) - to 
read/resize the jpeg files and build a time lapse mp4 video
+ Namedtuple, imported from the builtin module Collections - just to
practice the useful syntax and capabilities of this data structure
+ Requests - another builtin module used to retrieve the image from the url
+ Beautiful Soup (https://pypi.org/project/beautifulsoup4/) - imported but
not used at this stage

#### Main flow and automatisation of the app:
```
To do...
```
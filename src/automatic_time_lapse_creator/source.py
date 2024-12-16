class Source:
    """Contains two public attributes and four read-only attributes, which can be changed
    through the respective methods.

    Attributes::

        location_name: str - a folder with that name will be created on your pc. The videos
            for every day of the execution of the TimeLapseCreator will be created and put into
            subfolders into the "location_name" folder

        url: str - a valid web address where a webcam frame (image) should be located.
        
    ##### Be sure that the url does not point to a video resource."""

    def __init__(self, location_name: str, url: str) -> None:
        self.location_name: str = location_name
        self.url: str = url
        self._video_created: bool = False
        self._images_count: int = 0
        self._all_images_collected: bool = False
        self._images_partially_collected: bool = False

    @property
    def images_collected(self) -> bool:
        return self._all_images_collected

    @property
    def images_partially_collected(self) -> bool:
        return self._images_partially_collected

    @property
    def images_count(self) -> int:
        return self._images_count

    @property
    def video_created(self) -> bool:
        return self._video_created

    def set_video_created(self) -> None:
        """Set the video_created to True"""
        self._video_created = True

    def reset_video_created(self) -> None:
        """Reset the video_created to False"""
        self._video_created = False

    def increase_images(self) -> None:
        """Increases the count of the images by 1"""
        self._images_count += 1

    def reset_images_counter(self) -> None:
        """Resets the images count to 0"""
        self._images_count = 0

    def set_all_images_collected(self) -> None:
        """Sets the self._all_images_collected to True"""
        self._all_images_collected = True

    def set_images_partially_collected(self) -> None:
        """Sets the self._images_partially_collected to True"""
        self._images_partially_collected = True

    def reset_all_images_collected(self) -> None:
        """Resets the self._all_images_collected to False"""
        self._all_images_collected = False

    def reset_images_partially_collected(self) -> None:
        """Resets the self._images_partially_collected to False"""
        self._images_partially_collected = False

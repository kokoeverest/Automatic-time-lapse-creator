from glob import glob
from pathlib import Path
import cv2
import os
import logging
from .common.constants import JPG_FILE

logger = logging.getLogger(__name__)


class VideoManager:
    """A class for managing the time lapse from the collected images during the day.
    Contains three static methods for creating the video, deleting the image files
    and checking if a video file exists."""

    @classmethod
    def video_exists(cls, path: str | Path) -> bool:
        """Checks if a file exists at the specified path.

        Parameters::

            path: str | Path - the file path to be checked.

        Returns::

           bool - if the checked file exists or not."""

        return os.path.exists(path)

    @classmethod
    def create_timelapse(
        cls, path: str, output_video: str, fps: int, width: int, height: int
    ) -> bool:
        """Gets the image files from the specified folder and sorts them chronologically.
        Then a VideoWriter object creates the video and writes it to the specified folder.

        Parameters::

            path: str - the folder, containing the images
            output_video: str - the name of the video file to be created
            fps: int - frames per second of the video
            width: int - width of the video in pixels
            height: int - height of the video in pixels

        Returns::

            True - if the video was created successfully;
            False - in case of Exception during the creation of the video

        Note: the source image files are not modified or deleted in any case."""

        image_files = sorted(glob(f"{path}/*{JPG_FILE}"))

        if len(image_files) > 0:
            try:
                fourcc = cv2.VideoWriter.fourcc(*"mp4v")
                video_writer = cv2.VideoWriter(
                    output_video, fourcc, fps, (width, height)
                )

                for image_file in image_files:
                    img_path = os.path.join(path, image_file)

                    img = cv2.imread(img_path)
                    img = cv2.resize(src=img, dsize=(width, height))
                    video_writer.write(img)

                video_writer.release()
                logger.info(f"Video {output_video} created!")
                return True

            except Exception as exc:
                logger.error(exc, exc_info=True)
                return False
        else:
            logger.info(f"Folder {path} contained no images")
            return False

    @classmethod
    def delete_source_images(cls, path: str | Path) -> bool:
        """Deletes the image files from the specified folder.

        Parameters::

            path: str | Path - the folder path

        Returns::

            True - if the images were deleted successfully;
            False - in case of Exception during files deletion
        """

        image_files = glob(f"{path}/*{JPG_FILE}")
        try:
            logger.info(f"Deleting {len(image_files)} files from {path}")
            [os.remove(file) for file in image_files]
            return True
        except Exception as exc:
            logger.error(exc, exc_info=True)
            return False

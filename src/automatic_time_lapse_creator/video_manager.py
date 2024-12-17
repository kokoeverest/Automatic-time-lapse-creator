from glob import glob
from pathlib import Path
from datetime import datetime as dt
import cv2
import os
import logging
from .common.constants import (
    JPG_FILE,
    LOGGING_FORMAT,
    YYMMDD_FORMAT,
    HHMMSS_COLON_FORMAT,
    LOGS_DIR,
    LOG_FILE,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
cwd = os.getcwd()
Path(f"{cwd}{LOGS_DIR}").mkdir(exist_ok=True)
filename = Path(f"{cwd}{LOGS_DIR}/{dt.now().strftime(YYMMDD_FORMAT)}{LOG_FILE}")
date_fmt = f"{YYMMDD_FORMAT} {HHMMSS_COLON_FORMAT}"

logging.basicConfig(filename=filename, datefmt=date_fmt, format=LOGGING_FORMAT)


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
        cls,
        path: str,
        output_video: str,
        fps: int,
        width: int,
        height: int,
        with_stamp: bool = True,
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

                    if with_stamp:
                        date_time_text = f'{path[-10:]} {os.path.basename(image_file).rstrip(JPG_FILE).replace("_", ":")}'

                        # Add a rectangle for the date_time_text (black background)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.5
                        font_thickness = 1
                        text_size = cv2.getTextSize(
                            date_time_text, font, font_scale, font_thickness
                        )[0]
                        text_x, text_y = 10, 20  # Top-left corner of the text
                        rect_x2, rect_y2 = (
                            text_x + text_size[0] + 10,
                            text_y - text_size[1] - 10,
                        )

                        cv2.rectangle(
                            img,
                            (text_x, text_y),
                            (rect_x2, rect_y2),
                            (0, 0, 0),  # Black background
                            21,  # Curved shape of the rectangle
                        )

                        cv2.putText(
                            img,
                            date_time_text,
                            (text_x, text_y),  # Padding inside the rectangle
                            font,
                            font_scale,
                            (255, 255, 255),  # White text color
                            font_thickness,
                            lineType=cv2.LINE_AA,
                        )

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

        try:
            image_files = glob(f"{path}/*{JPG_FILE}")
            logger.info(f"Deleting {len(image_files)} files from {path}")
            [os.remove(file) for file in image_files]
            return True
        except Exception as exc:
            logger.error(exc, exc_info=True)
            return False

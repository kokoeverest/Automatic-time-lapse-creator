from glob import glob
from pathlib import Path
import cv2
import os
from logging import Logger
from math import ceil
from .common.constants import (
    JPG_FILE,
    DEFAULT_VIDEO_CODEC,
    BLACK_BACKGROUND,
    WHITE_TEXT,
    FILLED_RECTANGLE_VALUE,
)
from .common.utils import shorten


class VideoManager:
    """A class for managing the time lapse from the collected images during the day.
    Contains three static methods for creating the video, deleting the image files
    and checking if a video file exists."""

    @classmethod
    def video_exists(cls, path: str | Path) -> bool:
        """Checks if a file exists at the specified path.

        Args::

            path: str | Path - the file path to be checked.

        Returns::

           bool - if the checked file exists or not."""

        return os.path.exists(path)

    @classmethod
    def create_timelapse(
        cls,
        logger: Logger,
        path: str,
        output_video: str,
        fps: int,
        width: int,
        height: int,
        with_stamp: bool = True,
    ) -> bool:
        """Gets the image files from the specified folder and sorts them chronologically.
        Then a VideoWriter object creates the video and writes it to the specified folder.
        If the with_stamp is set to True (default) it will put a rectangle (containing the
        date and time of creation of the image) in the top left corner of every image.

        Args::

            logger: Logger - The logger instance for logging warnings, errors, and information.
            path: str - the folder, containing the images
            output_video: str - the name of the video file to be created
            fps: int - frames per second of the video
            width: int - width of the video in pixels
            height: int - height of the video in pixels
            with_stamp: bool - put the date and time text in the top left corner

        Returns::

            True - if the video was created successfully;
            False - in case of Exception during the creation of the video

        Note: the source image files are not modified or deleted in any case."""
        logger.info(f"Creating video from images in {shorten(path)}")
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
                        date_time_text = f"{path[-10:]} {os.path.basename(image_file).rstrip(JPG_FILE).replace('_', ':')}"

                        font_scale = width * 0.001
                        font_thickness = max(1, int(height * 0.004))

                        horizontal_padding = int(width * 0.02)
                        vertical_padding = int(height * 0.02)

                        font = cv2.FONT_HERSHEY_SIMPLEX
                        text_width, text_height = cv2.getTextSize(
                            date_time_text, font, font_scale, font_thickness
                        )[0]

                        text_position_left, text_position_up = (
                            ceil(width * 0.0001),
                            int(text_height * 1.2),
                        )
                        rect_top_left_x, rect_top_left_y = (
                            text_position_left - horizontal_padding // 2,
                            text_position_up - text_height - vertical_padding // 2,
                        )
                        rect_bottom_right_x, rect_bottom_right_y = (
                            text_position_left + text_width + horizontal_padding,
                            int((text_position_up + vertical_padding) * 1.2),
                        )

                        cv2.rectangle(
                            img,
                            (rect_top_left_x, rect_top_left_y),
                            (rect_bottom_right_x, rect_bottom_right_y),
                            BLACK_BACKGROUND,
                            FILLED_RECTANGLE_VALUE,
                        )
                        rectangle_padding = (
                            int(text_position_left * 5),
                            int(text_position_up * 1.3),
                        )

                        cv2.putText(
                            img,
                            date_time_text,
                            rectangle_padding,
                            font,
                            font_scale,
                            WHITE_TEXT,
                            font_thickness,
                            lineType=cv2.LINE_AA,
                        )

                    video_writer.write(img)

                video_writer.release()
                logger.info(f"Video created: {shorten(output_video)}")
                return True

            except Exception as exc:
                logger.error(exc, exc_info=True)
                return False
        else:
            logger.info(f"Folder contained no images {shorten(path)}")
            return False

    @classmethod
    def delete_source_media_files(
        cls,
        logger: Logger,
        path: str | Path,
        extension: str = JPG_FILE,
        delete_folder: bool = False,
    ) -> bool:
        """Deletes the image or video files from the specified folder.

        Args::

            logger: Logger - The logger instance for logging warnings, errors, and information.
            path: str | Path - the folder path
            extension: str - the file extension of the files intended for deletion
            delete_folder: bool - if the folder containing the files should also be deleted after 
                the files are deleted. The folder is deleted only if it's empty

        Returns::

            True - if the files were deleted successfully;
            False - in case of Exception during files deletion
        """
        path = Path(path)
        try:
            media_files = glob(f"{path}/*{extension}")
            logger.info(f"Deleting {len(media_files)} files from {shorten(str(path))}")
            [os.remove(file) for file in media_files]
            if delete_folder:
                files = os.listdir(path)
                if len(files) == 0:
                    try:
                        path.rmdir()
                        logger.info(f"Folder {shorten(str(path))} deleted!")
                    except PermissionError as exc:
                        logger.error(exc)
                    finally:
                        return True
                else:
                    logger.warning(f"Folder {shorten(str(path))} is not empty!")
            return True
        except Exception as exc:
            logger.error(exc, exc_info=True)
            return False

    @classmethod
    def create_monthly_summary_video(
        cls,
        logger: Logger,
        video_paths: list[str],
        output_video_path: str,
        fps: int,
        width: int,
        height: int,
    ) -> bool:
        """
        Creates a monthly summary video by concatenating a list of input videos.

        This method processes a list of video files and outputs a single video file
        to the specified location. The resulting video is created in the specified 
        resolution and frame rate.

        Args:
            logger (Logger): The logger instance for logging warnings, errors, and information.
            video_paths (list[str]): A list of video paths to the input videos.
            output_video_path (str): The path where the output video will be saved. If the video already
                exists, the method skips the operation.
            fps (int): Frames per second for the output video.
            width (int): Width of the output video in pixels.
            height (int): Height of the output video in pixels.

        Returns:
            bool: Returns True if the video is successfully created, otherwise False.
        """
        video_paths.sort()

        if cls.video_exists(output_video_path):
            logger.warning(f"Video exists, skipping... {shorten(output_video_path)}")
            return False
        video_parent_folder, _ = os.path.split(output_video_path)

        if not cls.video_exists(video_parent_folder):
            os.mkdir(video_parent_folder)
        try:
            fourcc = cv2.VideoWriter.fourcc(*DEFAULT_VIDEO_CODEC)
            output_video = cv2.VideoWriter(
                output_video_path, fourcc, fps, (width, height)
            )

            for video_path in video_paths:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    logger.warning(
                        f"Cannot open video: {shorten(video_path)}. Skipping..."
                    )
                    continue

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    output_video.write(frame)

                cap.release()

            output_video.release()
            return True
        except Exception as exc:
            logger.error(exc, exc_info=True)
            return False

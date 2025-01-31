from glob import glob
from pathlib import Path
import cv2
import os
import numpy as np
from logging import Logger
from .common.constants import (
    JPG_FILE,
    DEFAULT_VIDEO_CODEC,
    BLACK_BACKGROUND,
    WHITE_TEXT,
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
                # Read the first image to determine the correct height
                first_image = cv2.imread(image_files[0])
                if first_image is None:
                    logger.error(
                        f"Could not read first image: {shorten(image_files[0])}"
                    )
                    return False

                height, width, _ = first_image.shape

                fourcc = cv2.VideoWriter.fourcc(*"mp4v")
                video_writer = cv2.VideoWriter(
                    output_video, fourcc, fps, (width, height)
                )

                for image_file in image_files:
                    img_path = os.path.join(path, image_file)

                    img = cv2.imread(img_path)
                    # img = cv2.resize(src=img, dsize=(width, height))

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

    @classmethod
    def save_image_with_weather_overlay(
        cls,
        image_bytes: bytes,
        save_path: str,
        width: int,
        height: int,
        date_time_text: str = "",
        weather_data_text: str | None = None,
    ):
        """
        Saves an image from bytes data with an additional overlay containing weather information at the top.

        Args:
            image_bytes: bytes - Image data received from a request (response.content).
            save_path: str - Path where the new image will be saved.
            width: int - Width of the final image.
            height: int - Height of the final image (excluding overlay).
            date_time_text: str - The timestamp to be displayed (YYYY-MM-DD H:M:S).
            weather_data_text: str | None - The text for weather data, defaults to None.
        """

        # Convert bytes to an OpenCV image
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Ensure the image is properly loaded
        if img is None:
            return False
        img = cv2.resize(img, (width, height))

        overlay_text = date_time_text if weather_data_text is None else f"{date_time_text} | {weather_data_text}"

        # Define font settings
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_thickness = max(1, int(height * 0.004))
        font_scale = width * 0.0007
        text_size = cv2.getTextSize(overlay_text, font, font_scale, font_thickness)[0]

        # Define overlay rectangle dimensions
        overlay_height = int(text_size[1] * 2.5)  # Extra padding
        overlay_width = width
        overlay = np.full(
            (overlay_height, overlay_width, 3), BLACK_BACKGROUND, dtype=np.uint8
        )  # Black rectangle

        # Position text in the overlay
        text_x = int(width * 0.02)  # Small left margin
        text_y = int(overlay_height * 0.7)  # Centered vertically

        cv2.putText(
            overlay,
            overlay_text,
            (text_x, text_y),
            font,
            font_scale,
            WHITE_TEXT,
            font_thickness,
            lineType=cv2.LINE_AA,
        )

        # Stack overlay on top of the image
        final_image = np.vstack((overlay, img))

        # Save the image
        cv2.imwrite(save_path, final_image)

        return True

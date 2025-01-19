from glob import glob
from pathlib import Path
import cv2
import os
from logging import Logger
from .common.constants import JPG_FILE, DEFAULT_VIDEO_CODEC
from .common.utils import shorten


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

        Parameters::

            path: str | Path - the folder path

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
                    path.rmdir()

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

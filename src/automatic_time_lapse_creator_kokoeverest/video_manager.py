from glob import glob
from pathlib import Path
import cv2
import os
from src.automatic_time_lapse_creator_kokoeverest.common.constants import JPG_FILE


class VideoManager:
    """"""

    @classmethod
    def video_exists(cls, path: str | Path):
        """"""

        return os.path.exists(path)

    @classmethod
    def create_timelapse(cls, path: str, output_video: str, fps: int=30, width: int=640, height: int=360):
        """"""

        image_files = sorted(glob(f"{path}/*{JPG_FILE}"))

        try:
            fourcc = cv2.VideoWriter.fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

            for image_file in image_files:
                img_path = os.path.join(path, image_file)

                img = cv2.imread(img_path)
                img = cv2.resize(src=img, dsize=(width, height))
                video_writer.write(img)

            video_writer.release()
            print(f"Video {output_video} created!")
            return True

        except Exception:
            return False

    @classmethod
    def delete_source_images(cls, path: str | Path):
        """"""

        image_files = glob(f"{path}/*{JPG_FILE}")
        try:
            print(f"Deleting {len(image_files)} files from {path}")
            [os.remove(file) for file in image_files]
            return True
        except Exception:
            return False

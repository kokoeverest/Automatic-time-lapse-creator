from glob import glob
import cv2
import os


class VideoManager:
    """"""

    @classmethod
    def video_exists(path):
        """"""

        return os.path.exists(path)

    @classmethod
    def create_timelapse(path, output_video, fps=30, width=640, height=360):
        """"""
        
        image_files = sorted(glob(f"{path}/*.jpg"))

        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
            video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

            for image_file in image_files:
                img_path = os.path.join(path, image_file)

                img = cv2.imread(img_path)
                img = cv2.resize(img, (width, height))
                video_writer.write(img)

            video_writer.release()
            print(f"Video {output_video} created!")
            return True

        except Exception:
            return False

    @classmethod
    def delete_source_images(path):
        """"""
        
        image_files = glob(f"{path}/*.jpg")
        try:
            print(f"Deleting {len(image_files)} files from {path}")
            [os.remove(file) for file in image_files]
            return True
        except Exception:
            return False

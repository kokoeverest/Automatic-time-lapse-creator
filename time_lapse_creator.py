from glob import glob
import cv2
import os


def video_exists(path):
    return os.path.exists(path)


def create_timelapse(path, output_video, fps=24, width=640, height=360):
    image_files = sorted(glob(f'{path}/*.jpg'))

    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
        video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        for image_file in image_files:
            img_path = os.path.join(path, image_file)
            
            img = cv2.imread(img_path)
            img = cv2.resize(img, (width, height))
            video_writer.write(img)
        
        video_writer.release()
        return True
    
    except:
        return False
    

def delete_source_images(path):
    image_files = glob(f'{path}/*.jpg')
    try:
        [os.remove(file) for file in image_files]
        return True
    except:
        return False
    
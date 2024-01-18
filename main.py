import cv2
import requests
from datetime import datetime as dt, timedelta as td
from time import sleep
from bs4 import BeautifulSoup as bs
from collections import namedtuple
from pathlib import Path
from time_lapse_creator import create_timelapse, video_exists, delete_source_images
from time_management import s_set, s_rise


def collect_images_from_webcams():
    if not daylight:
        return False
    
    print(f'Start collecting images: {dt.now()}')
    while daylight:
        for site in sources_list:
            result = requests.get(site.url)
            img = result.content

            prefix = site.prefix
            file_name = dt.now().strftime("%H:%M:%S")
            current_path = f'{base_path}/{prefix}/{folder_name}'
            
            Path(current_path).mkdir(parents=True, exist_ok=True)
            if img:
                with open(f'{current_path}/{file_name}.jpg', "wb") as file:
                    file.write(img)
        sleep(60)
    print(f'Finished collecting for today: {dt.now()}') 
    return True


def is_daylight():
    return start < dt.now() < end

Source = namedtuple('Source', 'prefix url')

sources_list: list[Source] = [
    Source('aleko', 'https://home-solutions.bg/cams/aleko2.jpg?1705293967111'),
    Source('markudjik', 'https://media.borovets-bg.com/cams/channel?channel=31'),
    Source('plevenhut', 'https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718'),
    # Source('todorka', 'https://www.banskoski.com/ext/webcams/livecam-2.jpg'), # camera moving, bad video result
    
    ]

year, month, today = dt.today().year, dt.today().month, dt.today().day
start_hour, start_minutes = s_rise()
end_hour, end_minutes = s_set()
start = dt(year=year, month=month, day=today, hour=start_hour, minute=start_minutes)
end = dt(year=year, month=month, day=today, hour=end_hour, minute=end_minutes)

base_path = '/home/kaloyan/timelapse_test'
folder_name = dt.today().strftime('%Y-%m-%d')

daylight = is_daylight()

while True:
    images_collected = collect_images_from_webcams()

    if dt.now() > end and images_collected:
        for src in sources_list:
            input_folder = f'{base_path}/{src.prefix}/{folder_name}'
            output_video = f'{input_folder}/{folder_name}.mp4'
            if not video_exists(output_video):
                created = create_timelapse(input_folder, output_video)

            if created:
                deleted = delete_source_images(input_folder)
    else:
        print(f"Not daylight yet: {dt.now()}")
        sleep(300)
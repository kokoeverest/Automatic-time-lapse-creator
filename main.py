import requests
from datetime import datetime as dt
from time import sleep
from collections import namedtuple
from pathlib import Path
from time_lapse_creator import create_timelapse, video_exists, delete_source_images
from time_management import is_daylight, end_of_daylight 


def verify_request(site):
    try:
        response = requests.get(site.url)
        if 200 != response.status_code:
            raise Exception(f'Status code {response.status_code} is not 200')
        
        return response.content
    except Exception as e:
        raise Exception(str(e))


def collect_images_from_webcams():
    if is_daylight():
        print(f'Start collecting images: {dt.now()}')
        while is_daylight():
            for site in sources_list:
                try:
                    img = verify_request(site)

                    location = site.location
                    file_name = dt.now().strftime("%H:%M:%S")
                    current_path = f'{base_path}/{location}/{folder_name}'
                    
                    Path(current_path).mkdir(parents=True, exist_ok=True)
                    if img:
                        with open(f'{current_path}/{file_name}.jpg', "wb") as file:
                            file.write(img)
                except Exception as e:
                    print(str(e))
                    continue

            sleep(60)
        print(f'Finished collecting for today: {dt.now()}')
        return True
    
    return False


Source = namedtuple('Source', ['location', 'url'])

sources_list: list[Source] = [
    Source('aleko', 'https://home-solutions.bg/cams/aleko2.jpg?1705293967111'),
    Source('markudjik', 'https://media.borovets-bg.com/cams/channel?channel=31'),
    Source('plevenhut', 'https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718'),
]
base_path = '/home/kaloyan/timelapse_test'
folder_name = dt.today().strftime('%Y-%m-%d')

while True:
    images_collected = collect_images_from_webcams()

    if dt.now() > end_of_daylight and images_collected:
        for src in sources_list:
            input_folder = f'{base_path}/{src.location}/{folder_name}'
            output_video = f'{input_folder}/{folder_name}.mp4'

            if not video_exists(output_video):
                created = create_timelapse(input_folder, output_video)
            else:
                created = False

            if created:
                deleted = delete_source_images(input_folder)
    else:
        print(f"Not daylight yet: {dt.now()}")
        sleep(300)
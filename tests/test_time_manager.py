import os
from pathlib import Path
from src.automatic_time_lapse_creator_kokoeverest.video_manager import VideoManager as vm
from src.automatic_time_lapse_creator_kokoeverest.common.constants import JPG_FILE, MP4_FILE, YYMMDD_FORMAT, HHMMSS_UNDERSCORE_FORMAT # type: ignore
from datetime import datetime

cwd = os.getcwd()
# mock a video file to pass to the function
def test_video_manager_video_exists_returns_true_with_existing_video_file():
    assert vm.video_exists(cwd)


def test_video_manager_video_exists_returns_false_with_non_existing_path():
    assert not vm.video_exists(Path(f"{cwd}\\{datetime.now().strftime(YYMMDD_FORMAT)}{MP4_FILE}"))
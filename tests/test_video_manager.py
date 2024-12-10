import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.automatic_time_lapse_creator.video_manager import (
    VideoManager as vm,
)
from src.automatic_time_lapse_creator.common.constants import (
    YYMMDD_FORMAT,
    MP4_FILE,
    JPG_FILE,
)
from datetime import datetime
import tests.test_mocks as tm
from cv2 import VideoWriter

cwd = os.getcwd()


def test_video_manager_video_exists_returns_true_with_existing_video_file():
    # Arrange
    fake_file_path = f"fake/path/to/video_file{MP4_FILE}"

    # Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.video_manager.os.path"
    ) as mock_os_path:
        mock_os_path.exists.return_value = True
        assert vm.video_exists(fake_file_path)


def test_video_manager_video_exists_returns_false_with_non_existing_path():
    # Arrange
    fake_file_path = Path(f"{cwd}\\{datetime.now().strftime(YYMMDD_FORMAT)}{MP4_FILE}")

    # Act & Assert
    assert not vm.video_exists(fake_file_path)


def test_create_time_lapse_returns_False_when_images_folder_contains_no_images():
    # Arrange, Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.video_manager.glob",
        return_value=[],
    ):
        assert not vm.create_timelapse(
            tm.mock_path_to_images_folder,
            tm.mock_output_video_name,
            tm.mock_video_frames_per_second,
            tm.mock_video_width,
            tm.mock_video_height,
        )


def test_create_timelapse_success():
    # Arrange
    mock_writer = MagicMock(spec=VideoWriter)

    # Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.glob",
            return_value=tm.mock_images_list,
        ) as mock_glob,
        patch("cv2.VideoWriter", return_value=mock_writer),
        patch("cv2.imread", return_value=tm.mock_MatLike),
        patch("cv2.resize", return_value=tm.mock_MatLike),
    ):
        result = vm.create_timelapse(
            path=tm.mock_path_to_images_folder,
            output_video=tm.mock_output_video_name,
            fps=tm.mock_video_frames_per_second,
            width=tm.mock_video_width,
            height=tm.mock_video_height,
        )

    # Assert
    assert result
    mock_glob.assert_called_once_with(f"{tm.mock_path_to_images_folder}/*{JPG_FILE}")
    assert mock_writer.write.call_count == 10
    mock_writer.release.assert_called_once()

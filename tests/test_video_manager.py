from logging import Logger
import os
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
from src.automatic_time_lapse_creator.common.utils import shorten
from src.automatic_time_lapse_creator.video_manager import (
    VideoManager as vm,
)
from src.automatic_time_lapse_creator.common.constants import (
    YYMMDD_FORMAT,
    MP4_FILE,
    JPG_FILE,
    VIDEO_WIDTH_360p,
    VIDEO_HEIGHT_360p,
    DEFAULT_VIDEO_FPS,
)
from datetime import datetime
import tests.test_mocks as tm
import tests.test_data as td
from cv2 import VideoWriter

cwd = os.getcwd()
empty_list: list[Any] = []
emtpy_generetor: Generator[str, Any, None] = (x for x in empty_list)

@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=Logger)
    yield mock_logger
    mock_logger.reset_mock()


@pytest.fixture
def mock_video_paths():
    return ["video1.mp4", "video2.mp4", "video3.mp4"]


def test_video_exists_returns_true_with_existing_video_file():
    # Arrange
    fake_file_path = f"fake/path/to/video_file{MP4_FILE}"

    # Act & Assert
    with patch(
        "src.automatic_time_lapse_creator.video_manager.os.path"
    ) as mock_os_path:
        mock_os_path.exists.return_value = True
        assert vm.video_exists(fake_file_path)


def test_video_exists_returns_false_with_non_existing_path():
    # Arrange
    fake_file_path = Path(f"{cwd}\\{datetime.now().strftime(YYMMDD_FORMAT)}{MP4_FILE}")

    # Act & Assert
    assert not vm.video_exists(fake_file_path)


def test_create_time_lapse_returns_False_when_images_folder_contains_no_images(
    mock_logger: MagicMock,
):
    # Arrange, Act & Assert

    with patch("src.automatic_time_lapse_creator.video_manager.Path.glob", return_value=emtpy_generetor):
        assert not vm.create_timelapse(
            logger=mock_logger,
            path=tm.mock_path_to_images_folder,
            output_video=tm.mock_output_video_name,
            fps=tm.mock_video_frames_per_second,
        )
        assert mock_logger.info.call_count == 2


def test_create_timelapse_success(mock_logger: MagicMock):
    # Arrange
    mock_writer = MagicMock(spec=VideoWriter)

    # Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch("cv2.VideoWriter", return_value=mock_writer),
        patch("cv2.imread", return_value=tm.mock_MatLike),
    ):
        
        result = vm.create_timelapse(
            logger=mock_logger,
            path=tm.mock_path_to_images_folder,
            output_video=tm.mock_output_video_name,
            fps=tm.mock_video_frames_per_second,
        )

        # Assert
        assert result
        mock_glob.assert_called_once_with(f"*{JPG_FILE}")
        assert mock_writer.write.call_count == 10
        mock_writer.release.assert_called_once()
        assert mock_logger.info.call_count == 2


def test_create_timelapse_returns_False_if_first_image_is_None(mock_logger: MagicMock):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch("cv2.imread", return_value=None),
    ):
        result = vm.create_timelapse(
            logger=mock_logger,
            path=tm.mock_path_to_images_folder,
            output_video=tm.mock_output_video_name,
            fps=tm.mock_video_frames_per_second,
        )

        # Assert
        assert not result
        mock_glob.assert_called_once_with(f"*{JPG_FILE}")
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()


def test_create_timelapse_returns_False_if_exception_occurs(mock_logger: MagicMock):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch("cv2.VideoWriter", return_value=Exception),
    ):
        result = vm.create_timelapse(
            logger=mock_logger,
            path=tm.mock_path_to_images_folder,
            output_video=tm.mock_output_video_name,
            fps=tm.mock_video_frames_per_second,
        )

        # Assert
        assert not result
        mock_glob.assert_called_once_with(f"*{JPG_FILE}")
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()


def test_delete_source_media_files_returns_True_on_success(mock_logger: MagicMock):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.remove",
            return_value=None,
        ) as mock_remove,
    ):
        result = vm.delete_source_media_files(
            logger=mock_logger, path=tm.mock_path_to_images_folder
        )

        # Assert
        assert result
        assert mock_remove.call_count == 10
        mock_glob.assert_called_once_with(os.path.join(f"*{JPG_FILE}"))
        mock_logger.info.assert_called_once()


def test_delete_source_media_files_returns_True_and_warns_if_folder_is_not_empty(mock_logger: MagicMock):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.remove",
            return_value=None,
        ) as mock_remove,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.listdir",
            return_value=[""],
        ) as mock_listdir,
    ):
        result = vm.delete_source_media_files(
            logger=mock_logger, path=tm.mock_path_to_images_folder, delete_folder=True
        )

        # Assert
        assert result
        assert mock_remove.call_count == 10
        mock_listdir.assert_called_once_with(Path(tm.mock_path_to_images_folder))
        mock_glob.assert_called_once_with(
            os.path.join(f"*{JPG_FILE}")
        )
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called_once()


def test_delete_source_media_files_returns_True_if_folder_is_removed(
    mock_logger: MagicMock,
):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.remove",
            return_value=None,
        ) as mock_remove,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.listdir",
            return_value=[],
        ) as mock_listdir,
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.rmdir",
            return_value=[],
        ) as mock_rmdir,
    ):
        result = vm.delete_source_media_files(
            logger=mock_logger, path=tm.mock_path_to_images_folder, delete_folder=True
        )

        # Assert
        assert result
        assert mock_remove.call_count == 10
        mock_rmdir.assert_called_once()
        mock_listdir.assert_called_once_with(Path(tm.mock_path_to_images_folder))
        mock_glob.assert_called_once_with(
            os.path.join(f"*{JPG_FILE}")
        )
        assert mock_logger.info.call_count == 2


def test_delete_source_media_files_returns_True_in_case_of_PermissionError(
    mock_logger: MagicMock,
):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            return_value=tm.mock_images_iterator(),
        ) as mock_glob,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.remove",
            return_value=None,
        ) as mock_remove,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.listdir",
            return_value=[],
        ) as mock_listdir,
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.rmdir",
        side_effect=PermissionError("Permission denied")
        ) as mock_rmdir,
    ):
        result = vm.delete_source_media_files(
            logger=mock_logger, path=tm.mock_path_to_images_folder, delete_folder=True
        )

        # Assert
        assert result
        assert mock_remove.call_count == 10
        mock_rmdir.assert_called_once()
        mock_listdir.assert_called_once_with(Path(tm.mock_path_to_images_folder))
        mock_glob.assert_called_once_with(f"*{JPG_FILE}")
        assert mock_logger.info.call_count == 1
        assert mock_logger.error.call_count == 1


def test_delete_source_media_files_returns_False_on_Exception(mock_logger: MagicMock):
    # Arrange & Act
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.Path.glob",
            side_effect=Exception,
        ) as mock_glob,
        patch(
            "src.automatic_time_lapse_creator.video_manager.os.remove",
            side_effect=Exception,
        ) as mock_remove,
    ):
        result = vm.delete_source_media_files(
            logger=mock_logger, path=tm.mock_path_to_images_folder
        )

    # Assert
    assert not result
    assert mock_remove.call_count == 0
    mock_glob.assert_called_once_with(f"*{JPG_FILE}")
    mock_logger.error.assert_called_once()


def test_save_image_with_weather_overlay_saves_image_successfully():
    # Arrange
    with (
        patch(
            "cv2.imdecode", return_value=np.zeros((100, 100, 3), dtype=np.uint8)
        ) as mock_imdecode,
        patch(
            "cv2.resize", return_value=np.zeros((VIDEO_HEIGHT_360p, VIDEO_WIDTH_360p, 3), dtype=np.uint8)
        ) as mock_resize,
        patch("cv2.imwrite", return_value=True) as mock_imwrite,
    ):
        # Act
        result = vm.save_image_with_weather_overlay(
            tm.mock_bytes,
            tm.mock_save_file_path,
            VIDEO_WIDTH_360p,
            VIDEO_HEIGHT_360p,
            td.sample_date_time_text,
            td.sample_weather_data_text,
        )

        # Assert
        assert result
        mock_imdecode.assert_called_once()
        mock_resize.assert_called_once()
        mock_imwrite.assert_called_once()


def test_save_image_with_weather_overlay_handles_invalid_image():
    # Arrange
    invalid_bytes = b"invalid_bytes"

    with patch("cv2.imdecode", return_value=None) as mock_imdecode:
        # Act
        result = vm.save_image_with_weather_overlay(
            invalid_bytes, tm.mock_save_file_path, VIDEO_WIDTH_360p, VIDEO_HEIGHT_360p
        )

        # Assert
        assert not result
        mock_imdecode.assert_called_once()


def test_save_image_with_weather_overlay_handles_no_weather_data():
    # Arrange
    weather_data_text = None

    with (
        patch("cv2.imdecode", return_value=np.zeros((100, 100, 3), dtype=np.uint8)),
        patch("cv2.resize", return_value=np.zeros((VIDEO_HEIGHT_360p, VIDEO_WIDTH_360p, 3), dtype=np.uint8)),
        patch("cv2.getTextSize", return_value=((100, 20), 10)),
        patch("cv2.putText"),
        patch("cv2.imwrite", return_value=True) as mock_imwrite,
    ):
        # Act
        result = vm.save_image_with_weather_overlay(
            tm.mock_bytes,
            tm.mock_save_file_path,
            VIDEO_WIDTH_360p,
            VIDEO_HEIGHT_360p,
            td.sample_date_time_text,
            weather_data_text,
        )

        # Assert
        assert result
        mock_imwrite.assert_called_once()


def test_save_image_with_weather_overlay_fails_to_save():
    # Arrange
    

    with (
        patch("cv2.imdecode", return_value=np.zeros((100, 100, 3), dtype=np.uint8)),
        patch("cv2.resize", return_value=np.zeros((VIDEO_HEIGHT_360p, VIDEO_WIDTH_360p, 3), dtype=np.uint8)),
        patch("cv2.getTextSize", return_value=((100, 20), 10)),
        patch("cv2.putText"),
        patch("cv2.imwrite", return_value=False) as mock_imwrite,
    ):
        # Act
        result = vm.save_image_with_weather_overlay(
            tm.mock_bytes,
            tm.mock_save_file_path,
            VIDEO_WIDTH_360p,
            VIDEO_HEIGHT_360p,
            td.sample_date_time_text,
            td.sample_weather_data_text,
        )

        # Assert
        assert not result
        mock_imwrite.assert_called_once()


def test_create_monthly_summary_video_skips_if_output_exists2(
    mock_logger: MagicMock, mock_video_paths: list[str]
):
    with patch(
        "src.automatic_time_lapse_creator.video_manager.VideoManager.video_exists",
        return_value=True,
    ) as mock_exists:
        result = vm.create_monthly_summary_video(
            mock_logger, mock_video_paths, tm.mock_output_video_name, DEFAULT_VIDEO_FPS
        )

    assert not result
    mock_exists.assert_called_once_with(tm.mock_output_video_name)
    mock_logger.warning.assert_called_once_with(f"Video exists, skipping... {shorten(tm.mock_output_video_name)}")


def test_create_monthly_summary_video_creates_video_successfully(
    mock_logger: MagicMock, mock_video_paths: list[str]
):
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.VideoManager.video_exists",
            side_effect=[False, False],
        ),
        patch("src.automatic_time_lapse_creator.video_manager.os.mkdir"),
        patch("cv2.VideoCapture") as mock_capture,
        patch("cv2.VideoWriter") as mock_writer,
    ):
        mock_cap_instance = MagicMock()
        mock_capture.return_value = mock_cap_instance
        mock_cap_instance.isOpened.side_effect = [True, True, True]
        mock_cap_instance.read.side_effect = [
            (
                True,
                tm.mock_MatLike,
            ),  # First valid frame (initializes VideoWriter)
            (False, None),  # End of first video
            (True, tm.mock_MatLike),  # Second valid frame
            (False, None),  # End of second video
            (True, tm.mock_MatLike),  # Third valid frame
            (False, None),  # End of third video
        ]

        mock_video_writer_instance = MagicMock()
        mock_writer.return_value = mock_video_writer_instance

        result = vm.create_monthly_summary_video(
            mock_logger, mock_video_paths, tm.mock_output_video_name, DEFAULT_VIDEO_FPS
        )

    assert result
    mock_capture.assert_called()
    mock_writer.assert_called_once_with(
        tm.mock_output_video_name, mock_writer.fourcc(), DEFAULT_VIDEO_FPS, (tm.mock_MatLike.shape[1], tm.mock_MatLike.shape[0])
    )
    mock_video_writer_instance.write.assert_called()
    mock_video_writer_instance.release.assert_called_once()


def test_create_monthly_summary_video_skips_invalid_videos2(
    mock_logger: MagicMock, mock_video_paths: list[str]
):
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.VideoManager.video_exists",
            side_effect=[False, False],
        ),
        patch("src.automatic_time_lapse_creator.video_manager.os.mkdir", return_value=None),
        patch("cv2.VideoCapture") as mock_capture,
        patch("cv2.VideoWriter") as mock_writer,
    ):
        mock_cap_instance = MagicMock()
        mock_capture.return_value = mock_cap_instance
        mock_cap_instance.isOpened.side_effect = [
            False,
            True,
            False,
        ]  # First and third video fail
        mock_cap_instance.read.side_effect = [
            (True, tm.mock_MatLike),  # Second video valid frame
            (False, None),  # End of second video
        ]

        mock_video_writer_instance = MagicMock()
        mock_writer.return_value = mock_video_writer_instance

        result = vm.create_monthly_summary_video(
            mock_logger, mock_video_paths, tm.mock_output_video_name, DEFAULT_VIDEO_FPS
        )

    assert result
    mock_logger.warning.assert_any_call(f"Cannot open video: {shorten('video1.mp4')}. Skipping...")
    mock_logger.warning.assert_any_call(f"Cannot open video: {shorten('video3.mp4')}. Skipping...")
    mock_writer.assert_called_once()
    mock_video_writer_instance.release.assert_called_once()


def test_create_monthly_summary_video_returns_false_if_no_valid_videos(
    mock_logger: MagicMock,
):
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.VideoManager.video_exists",
            side_effect=[False, False],
        ),
        patch("src.automatic_time_lapse_creator.video_manager.os.mkdir"),
        patch("cv2.VideoCapture") as mock_capture,
    ):
        mock_cap_instance = MagicMock()
        mock_capture.return_value = mock_cap_instance
        mock_cap_instance.isOpened.return_value = False  # No video opens successfully

        result = vm.create_monthly_summary_video(
            mock_logger, ["video1.mp4", "video2.mp4"], tm.mock_output_video_name, DEFAULT_VIDEO_FPS
        )

    assert not result
    mock_logger.error.assert_called_once_with(
        "No valid videos found to create a summary."
    )


def test_create_monthly_summary_video_handles_exceptions(
    mock_logger: MagicMock, mock_video_paths: list[str]
):
    with (
        patch(
            "src.automatic_time_lapse_creator.video_manager.VideoManager.video_exists",
            side_effect=[False, False],
        ),
        patch("src.automatic_time_lapse_creator.video_manager.os.mkdir"),
        patch("cv2.VideoCapture", side_effect=Exception("Unexpected error")),
    ):
        result = vm.create_monthly_summary_video(
            mock_logger, mock_video_paths, tm.mock_output_video_name, DEFAULT_VIDEO_FPS
        )

    assert not result
    mock_logger.error.assert_called_once()

def test_create_monthly_summary_video_skips_if_output_exists(mock_logger: MagicMock, mock_video_paths: list[str]):
    # Act & Assert
    with patch("src.automatic_time_lapse_creator.video_manager.os.path.exists", return_value=True):
        assert not vm.create_monthly_summary_video(mock_logger, mock_video_paths, "output.mp4", mock_logger)

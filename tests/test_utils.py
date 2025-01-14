from src.automatic_time_lapse_creator.common.utils import shorten, create_log_message
from tests.test_data import sample_source1


def test_shorten_returns_correct_file_path():
    # Arrange
    file_path = "C:\\Users\\user\\Desktop\\Kofe\\Python\\automatic_time_lapse_creator\\Automatic-time-lapse-creator\\stara_planina\\mazalat_hut\\2025-01-07\\2025-01-07.mp4"
    expected = "stara_planina\\mazalat_hut\\2025-01-07\\2025-01-07.mp4"

    # Act
    result = shorten(file_path)

    # Assert
    assert result == expected


def test_shorten_returns_correct_folder_path():
    # Arrange
    folder_path = "C:\\Users\\user\\Desktop\\Kofe\\Python\\automatic_time_lapse_creator\\Automatic-time-lapse-creator\\stara_planina\\mazalat_hut\\2025-01-07"
    expected = "stara_planina\\mazalat_hut\\2025-01-07"

    # Act
    result = shorten(folder_path)

    # Assert
    assert result == expected


def test_create_log_message_returns_correct_message_for_add_method():
    # Arrange
    expected = f"Source with location: {sample_source1.location_name} or url: {sample_source1.url} already exists!"

    #  Act
    result = create_log_message(sample_source1.location_name, sample_source1.url, "add")

    # Assert
    assert expected == result


def test_create_log_message_returns_correct_message_for_remove_method():
    # Arrange
    expected = f"Source with location: {sample_source1.location_name} or url: {sample_source1.url} doesn't exist!"

    #  Act
    result = create_log_message(
        sample_source1.location_name, sample_source1.url, "remove"
    )

    # Assert
    assert expected == result


def test_create_log_message_returns_correct_message_for_unknown_method():
    # Arrange
    unknown_method = "adddd"
    expected = f"Unknown command: {unknown_method}"

    #  Act
    result = create_log_message(
        sample_source1.location_name, sample_source1.url, unknown_method
    )

    # Assert
    assert expected == result

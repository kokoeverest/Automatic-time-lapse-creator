import pytest
import tests.test_data as td
from src.automatic_time_lapse_creator.source import Source


@pytest.fixture
def sample_source():
    return td.sample_source1


def test_source_initializes_correctly(sample_source: Source):
    # Arrange, Act & Assert
    assert isinstance(sample_source, Source)
    assert sample_source.location_name == td.valid_source_name
    assert sample_source.url == td.valid_url
    assert not sample_source.video_created
    assert sample_source.images_count == 0
    assert not sample_source.images_collected
    assert not sample_source.images_partially_collected


def test_set_video_created_changes_video_created_to_True(sample_source: Source):
    # Arrange & Act
    sample_source.set_video_created()

    # Assert
    assert sample_source.video_created


def test_reset_video_created_changes_video_created_to_False(sample_source: Source):
    # Arrange & Act
    sample_source.reset_video_created()

    # Assert
    assert not sample_source.video_created


def test_increase_images_increases_the_images_count_by_one(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()

    # Assert
    assert sample_source.images_count == 1


def test_reset_images_counter_resets_the_images_count_to_zero(sample_source: Source):
    # Arrange & Act
    sample_source.increase_images()
    sample_source.reset_images_counter()

    # Assert
    assert sample_source.images_count == 0


def test_set_all_images_collected_sets_all_images_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_all_images_collected()

    # Assert
    assert sample_source.images_collected


def test_reset_all_images_collected_resets_all_images_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_all_images_collected()

    # Assert
    assert not sample_source.images_collected


def test_set_images_partially_collected_sets_images_partially_collected_to_True(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.set_images_partially_collected()

    # Assert
    assert sample_source.images_partially_collected


def test_reset_images_partially_collected_resets_images_partially_collected_to_False(
    sample_source: Source,
):
    # Arrange & Act
    sample_source.reset_images_partially_collected()

    # Assert
    assert not sample_source.images_partially_collected

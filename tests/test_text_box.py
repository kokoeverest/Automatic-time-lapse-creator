import pytest
import numpy as np
from cv2.typing import MatLike

from src.automatic_time_lapse_creator.text_box import (
    TopOutsideTextBox,
    TopInsideTextBox,
    BottomInsideTextBox,
    BottomOutsideTextBox,
)

@pytest.fixture
def mock_image():
    return np.zeros((600, 800, 3), dtype=np.uint8)

def test_top_outside_text_box(mock_image: MatLike):
    # Arrange
    text_box = TopOutsideTextBox("Test", 800, 600)
    
    # Act
    result = text_box.position(mock_image)
    
    # Assert
    assert result.shape[0] == mock_image.shape[0] + text_box.height
    assert result.shape[1] == mock_image.shape[1]

def test_top_inside_text_box(mock_image: MatLike):
    # Arrange
    text_box = TopInsideTextBox("Test", 800, 600)
    
    # Act
    result = text_box.position(mock_image)
    
    # Assert
    assert result.shape == mock_image.shape

def test_bottom_inside_text_box(mock_image: MatLike):
    # Arrange
    text_box = BottomInsideTextBox("Test", 800, 600)
    
    # Act
    result = text_box.position(mock_image)
    
    # Assert
    assert result.shape == mock_image.shape

def test_bottom_outside_text_box(mock_image: MatLike):
    # Arrange
    text_box = BottomOutsideTextBox("Test", 800, 600)
    
    # Act
    result = text_box.position(mock_image)
    
    # Assert
    assert result.shape[0] == mock_image.shape[0] + text_box.height
    assert result.shape[1] == mock_image.shape[1]

def test_blend_with_image(mock_image: MatLike):
    # Arrange
    text_box = TopInsideTextBox("Test", 800, 600)
    
    # Act
    blended_image = text_box.blend_with_image(mock_image, 0)
    
    # Assert
    assert blended_image.shape == mock_image.shape

def test_remove_alpha_channel_for_vstack():
    # Arrange
    text_box = TopOutsideTextBox("Test", 800, 600)
    
    # Act
    result = text_box._remove_alpha_channel_for_vstack()
    
    # Assert
    assert result.shape[2] == 3

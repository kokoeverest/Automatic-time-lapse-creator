import numpy as np
import cv2
from abc import ABC, abstractmethod
from .common.constants import BLACK_BACKGROUND, WHITE_TEXT
from cv2.typing import MatLike


class TextBox(ABC):
    """Abstract base class for text overlays on images with transparency support."""
    TRANSPARENCY_HIGH: float = 0.3
    TRANSPARENCY_MID: float = 0.5
    TRANSPARENCY_LOW: float = 0.7
    TRANSPARENCY_NO: float = 1

    def __init__(
        self,
        text: str,
        img_width: int,
        img_height: int,
        box_transparency: float = TRANSPARENCY_MID,
        bg_color: tuple[int] = BLACK_BACKGROUND,
        text_color: tuple[int] = WHITE_TEXT,
    ):
        """_summary_

        Args:
            text (str): _description_
            img_width (int): _description_
            img_height (int): _description_
            box_transparency (float, optional): _description_. Defaults to transparency_mid.
            bg_color (tuple[int], optional): _description_. Defaults to BLACK_BACKGROUND.
            text_color (tuple[int], optional): _description_. Defaults to WHITE_TEXT.
        """
        self.text = text
        self.width = img_width
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = img_width * 0.0007
        self.font_thickness = max(1, int(img_height * 0.004))
        self.bg_color = bg_color
        self.text_color = text_color
        self.alpha = box_transparency

        self.text_size = cv2.getTextSize(self.text, self.font, self.font_scale, self.font_thickness)[0]
        self.height = int(self.text_size[1] * 2.5)

        self.box = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.box[:, :, :3] = self.bg_color  # Fill the background color (BGR part)
        self.box[:, :, 3] = int(self.alpha * 255)  # Set alpha (transparency)

        # Create a BGR copy to render text (since OpenCV does not support text on BGRA)
        rectangle = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)

        # Calculate text position
        self.text_x = int(self.width * 0.02)
        self.text_y = int(self.height * 0.7)

        cv2.putText(
            rectangle, 
            self.text, 
            (self.text_x, self.text_y), 
            self.font, 
            self.font_scale, 
            self.text_color, 
            self.font_thickness, 
            lineType=cv2.LINE_AA
        )

        # Merge the text layer into the main box (preserve alpha)
        self.box[:, :, :3] = rectangle

    @abstractmethod
    def position(self, img: MatLike) -> MatLike:
        """Abstract method for positioning the text box on an image."""
        pass

    def _remove_alpha_channel_for_vstack(self):
        """Removes the transparency alpha channel for vstack

        Returns:
            @Self: the sliced self.box
        """
        return self.box[:, :, :3]

    def blend_with_image(self, img: MatLike, y_offset: int) -> MatLike:
        """Blends the text box with transparency into the given image."""
        final_image = img.copy()

        # Extract the alpha channel
        alpha_mask = self.box[:, :, 3] / 255.0  # Normalize to range 0-1
        inv_alpha_mask = 1.0 - alpha_mask  # Inverted mask

        # Blend each color channel
        for ch in range(3):  # B, G, R channels
            final_image[y_offset : y_offset + self.height, :, ch] = (
                inv_alpha_mask * final_image[y_offset : y_offset + self.height, :, ch]
                + alpha_mask * self.box[:, :, ch]
            ).astype(np.uint8)

        return final_image


class TopOutsideTextBox(TextBox):
    """Text box positioned outside and above the image."""

    def position(self, img: MatLike) -> MatLike:
        text_box_bgr = self._remove_alpha_channel_for_vstack()
        return np.vstack((text_box_bgr, img))


class TopInsideTextBox(TextBox):
    """Text box positioned inside the image at the top."""

    def position(self, img: MatLike) -> MatLike:
        return self.blend_with_image(img, y_offset=0)


class BottomInsideTextBox(TextBox):
    """Text box positioned inside the image at the bottom."""

    def position(self, img: MatLike) -> MatLike:
        return self.blend_with_image(img, y_offset=img.shape[0] - self.height)


class BottomOutsideTextBox(TextBox):
    """Text box positioned outside and below the image."""

    def position(self, img: MatLike) -> MatLike:
        text_box_bgr = self._remove_alpha_channel_for_vstack()
        return np.vstack((img, text_box_bgr))

from abc import ABC, abstractmethod
from typing import Sequence
from cv2.typing import MatLike
from numpy.typing import NDArray
from numpy import uint8


BLACK_BACKGROUND: tuple[int, int, int]
WHITE_TEXT: tuple[int, int, int]

class TextBox(ABC):
    TRANSPARENCY_HIGH: float
    TRANSPARENCY_MID: float
    TRANSPARENCY_LOW: float
    TRANSPARENCY_NO: float

    text: str
    width: int
    height: int
    font: int
    font_scale: float
    font_thickness: int
    bg_color: tuple[int]
    text_color: tuple[int]
    alpha: float
    text_size: Sequence[int]
    box: MatLike
    text_x: int
    text_y: int

    def __init__(
        self,
        text: str,
        img_width: int,
        img_height: int,
        box_transparency: float = ...,
        bg_color: tuple[int, int, int] = ...,
        text_color: tuple[int, int, int] = ...,
    ) -> None: ...

    @abstractmethod
    def position(self, img: MatLike) -> MatLike: ...

    def _remove_alpha_channel_for_vstack(self) -> NDArray[uint8]: ...

    def blend_with_image(self, img: MatLike, y_offset: int) -> MatLike: ...

class TopOutsideTextBox(TextBox):
    def position(self, img: MatLike) -> MatLike: ...

class TopInsideTextBox(TextBox):
    def position(self, img: MatLike) -> MatLike: ...

class BottomInsideTextBox(TextBox):
    def position(self, img: MatLike) -> MatLike: ...

class BottomOutsideTextBox(TextBox):
    def position(self, img: MatLike) -> MatLike: ...
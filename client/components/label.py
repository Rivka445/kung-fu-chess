import cv2
import numpy as np
from client.graphics.theme import FONT, WHITE_TXT


from client.components.base import UIComponent


class Label(UIComponent):
    def __init__(self, x: int, y: int, text: str,
                 scale: float = 0.5, color: tuple = WHITE_TXT):
        self.x, self.y = x, y
        self.text  = text
        self.scale = scale
        self.color = color

    def draw(self, canvas: np.ndarray) -> None:
        cv2.putText(canvas, self.text, (self.x, self.y),
                    FONT, self.scale, self.color, 1, cv2.LINE_AA)

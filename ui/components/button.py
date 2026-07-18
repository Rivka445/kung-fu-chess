import cv2
import numpy as np
from ui.graphics.theme import FONT, PANEL_BG, WHITE_TXT, GOLD


class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.text = text

    def is_clicked(self, mx: int, my: int) -> bool:
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def draw(self, canvas: np.ndarray) -> None:
        cv2.rectangle(canvas, (self.x, self.y), (self.x + self.w, self.y + self.h), PANEL_BG, -1)
        cv2.rectangle(canvas, (self.x, self.y), (self.x + self.w, self.y + self.h), GOLD, 1)
        tx = self.x + (self.w - len(self.text) * 9) // 2
        ty = self.y + self.h // 2 + 5
        cv2.putText(canvas, self.text, (tx, ty), FONT, 0.5, WHITE_TXT, 1, cv2.LINE_AA)

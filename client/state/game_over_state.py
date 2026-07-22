import cv2
import numpy as np
from client.state.base import UIState
from client.components.button import Button
from client.components.label import Label
from client.components.container import UIContainer
from client.graphics.theme import GOLD, DARK_BG

FADE_IN_MS = 400  # how long the reveal-from-black takes when this screen appears


class GameOverState(UIState):
    def __init__(self, on_restart, on_quit, canvas_w: int, canvas_h: int):
        cx = canvas_w // 2
        cy = canvas_h // 2
        self._title      = Label(cx - 90, cy - 60, "GAME OVER", scale=1.2, color=(0, 0, 255, 255))
        self._btn_again  = Button(cx - 80, cy,      160, 45, "Play Again")
        self._btn_quit   = Button(cx - 80, cy + 65, 160, 45, "Quit")
        self._on_restart = on_restart
        self._on_quit    = on_quit
        self._elapsed_ms = 0

        # Composite Pattern: Add components to a container
        self._container = UIContainer()
        self._container.add(self._title)
        self._container.add(self._btn_again)
        self._container.add(self._btn_quit)

    def on_enter(self) -> None:
        self._elapsed_ms = 0

    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None:
        if event.get("type") != "click":
            return
        mx, my = event["x"], event["y"]
        if self._btn_again.is_clicked(mx, my):
            self._on_restart()
        elif self._btn_quit.is_clicked(mx, my):
            self._on_quit()

    def update(self, ms: int) -> None:
        self._elapsed_ms = min(FADE_IN_MS, self._elapsed_ms + ms)

    def draw(self, canvas: np.ndarray) -> None:
        self._container.draw(canvas)
        progress = self._elapsed_ms / FADE_IN_MS
        if progress < 1.0:
            # Reveal the screen out of black instead of popping in instantly.
            overlay = canvas.copy()
            overlay[:] = DARK_BG[:3]
            alpha = 1.0 - progress
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

import numpy as np
from ui.state.base import UIState
from ui.components.button import Button
from ui.components.label import Label
from ui.graphics.theme import GOLD


class GameOverState(UIState):
    def __init__(self, on_restart, on_quit, canvas_w: int, canvas_h: int):
        cx = canvas_w // 2
        cy = canvas_h // 2
        self._title      = Label(cx - 90, cy - 60, "GAME OVER", scale=1.2, color=(0, 0, 255, 255))
        self._btn_again  = Button(cx - 80, cy,      160, 45, "Play Again")
        self._btn_quit   = Button(cx - 80, cy + 65, 160, 45, "Quit")
        self._on_restart = on_restart
        self._on_quit    = on_quit

    def on_enter(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None:
        if event.get("type") != "click":
            return
        mx, my = event["x"], event["y"]
        if self._btn_again.is_clicked(mx, my):
            self._on_restart()
        elif self._btn_quit.is_clicked(mx, my):
            self._on_quit()

    def update(self, ms: int) -> None: pass

    def draw(self, canvas: np.ndarray) -> None:
        self._title.draw(canvas)
        self._btn_again.draw(canvas)
        self._btn_quit.draw(canvas)

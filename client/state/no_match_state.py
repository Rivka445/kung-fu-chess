import numpy as np
from client.state.base import UIState
from client.components.button import Button
from client.components.label import Label
from client.components.container import UIContainer
from client.graphics.theme import GOLD


class NoMatchState(UIState):
    """Shown when a search (SearchingState) times out after 60s with no opponent found."""

    def __init__(self, on_back, canvas_w: int, canvas_h: int):
        cx = canvas_w // 2
        cy = canvas_h // 2
        self._title   = Label(cx - 130, cy - 40, "Couldn't find an opponent", scale=0.7, color=GOLD)
        self._btn_ok  = Button(cx - 80, cy, 160, 45, "OK")
        self._on_back = on_back

        # Composite Pattern: Add components to a container
        self._container = UIContainer()
        self._container.add(self._title)
        self._container.add(self._btn_ok)

    def on_enter(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None:
        if event.get("type") != "click":
            return
        mx, my = event["x"], event["y"]
        if self._btn_ok.is_clicked(mx, my):
            self._on_back()

    def update(self, ms: int) -> None: pass

    def draw(self, canvas: np.ndarray) -> None:
        self._container.draw(canvas)

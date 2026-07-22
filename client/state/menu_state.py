import numpy as np
from client.state.base import UIState
from client.components.button import Button
from client.components.label import Label
from client.components.container import UIContainer
from client.graphics.theme import GOLD


class MenuState(UIState):
    def __init__(self, on_start, on_quit, canvas_w: int, canvas_h: int, on_play=None):
        cx = canvas_w // 2
        cy = canvas_h // 2
        self._title = Label(cx - 120, cy - 80, "KUNG-FU CHESS", scale=1.2, color=GOLD)
        # Online (--ws) mode passes on_play and shows "Play" (ELO matchmaking);
        # local hot-seat mode leaves on_play unset and shows "Start Game".
        primary_label = "Play" if on_play is not None else "Start Game"
        self._btn_primary = Button(cx - 80, cy - 20, 160, 45, primary_label)
        self._btn_quit    = Button(cx - 80, cy + 45, 160, 45, "Quit")
        self._on_primary  = on_play if on_play is not None else on_start
        self._on_quit     = on_quit

        # Composite Pattern: Add components to a container
        self._container = UIContainer()
        self._container.add(self._title)
        self._container.add(self._btn_primary)
        self._container.add(self._btn_quit)

    def on_enter(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None:
        if event.get("type") != "click":
            return
        mx, my = event["x"], event["y"]
        if self._btn_primary.is_clicked(mx, my):
            self._on_primary()
        elif self._btn_quit.is_clicked(mx, my):
            self._on_quit()

    def update(self, ms: int) -> None: pass

    def draw(self, canvas: np.ndarray) -> None:
        self._container.draw(canvas)

import numpy as np
from ui.state.base import UIState
from ui.components.label import Label
from ui.components.container import UIContainer
from ui.graphics.theme import GOLD


class SearchingState(UIState):
    """
    Shown after clicking Play. The actual matchmaking (ELO ±100, up to 60s)
    runs server-side; this screen just shows progress while the bridge's
    background thread waits for a match or a NO_MATCH timeout.
    """

    def __init__(self, bridge, canvas_w: int, canvas_h: int):
        cx = canvas_w // 2
        cy = canvas_h // 2
        self._bridge = bridge
        self._title   = Label(cx - 150, cy - 20, "Searching for an opponent...", scale=0.7, color=GOLD)
        self._elapsed = Label(cx - 20, cy + 20, "0s")
        self._elapsed_ms = 0

        # Composite Pattern: Add components to a container
        self._container = UIContainer()
        self._container.add(self._title)
        self._container.add(self._elapsed)

    def on_enter(self) -> None:
        self._elapsed_ms = 0
        self._bridge.start_search()

    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None: pass

    def update(self, ms: int) -> None:
        self._elapsed_ms += ms
        self._elapsed.text = f"{self._elapsed_ms // 1000}s"

    def draw(self, canvas: np.ndarray) -> None:
        self._container.draw(canvas)

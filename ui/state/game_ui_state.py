from ui.state.base import UIState
from ui.server_bridge.base import ServerBridge


class GameUIState(UIState):
    def __init__(self, bridge: ServerBridge):
        self._bridge = bridge

    def on_enter(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None: pass

    def update(self, ms: int) -> None:
        self._bridge.advance_time(ms)

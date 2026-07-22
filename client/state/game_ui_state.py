from client.state.base import UIState
from client.engine_bridge.base import EngineBridge


class GameUIState(UIState):
    def __init__(self, bridge: EngineBridge):
        self._bridge = bridge

    def on_enter(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_input(self, event: dict) -> None: pass

    def update(self, ms: int) -> None:
        self._bridge.advance_time(ms)

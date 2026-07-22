from client.state.base import UIState


class StateManager:
    def __init__(self, initial: UIState):
        self._current = initial
        self._current.on_enter()

    @property
    def current(self) -> UIState:
        return self._current

    def transition(self, new_state: UIState) -> None:
        self._current.on_exit()
        self._current = new_state
        self._current.on_enter()

    def handle_input(self, event: dict) -> None:
        self._current.handle_input(event)

    def update(self, ms: int) -> None:
        self._current.update(ms)

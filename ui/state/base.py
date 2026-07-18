from abc import ABC, abstractmethod


class UIState(ABC):
    @abstractmethod
    def on_enter(self) -> None: ...

    @abstractmethod
    def on_exit(self) -> None: ...

    @abstractmethod
    def handle_input(self, event: dict) -> None: ...

    @abstractmethod
    def update(self, ms: int) -> None: ...

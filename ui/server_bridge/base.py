from abc import ABC, abstractmethod
from core.model.position import Position
from core.model.board import Board
from core.model.game_state import GameState


class ServerBridge(ABC):
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def send_move(self, source: Position, target: Position) -> None: ...

    @abstractmethod
    def send_jump(self, pos: Position) -> None: ...

    @abstractmethod
    def get_board(self) -> Board: ...

    @abstractmethod
    def get_state(self) -> GameState: ...

    @abstractmethod
    def advance_time(self, ms: int) -> None: ...

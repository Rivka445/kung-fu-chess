from abc import ABC, abstractmethod
from shared.model.position import Position
from shared.model.board import Board
from shared.model.game_state import GameState


class EngineBridge(ABC):
    @abstractmethod
    def login(self) -> None: ...

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

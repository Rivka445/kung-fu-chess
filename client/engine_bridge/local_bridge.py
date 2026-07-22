from client.engine_bridge.base import EngineBridge
from core.engine.game_engine import GameEngine
from core.model.position import Position
from core.model.board import Board
from core.model.game_state import GameState


class LocalBridge(EngineBridge):
    """Local implementation — talks directly to GameEngine, no network."""

    def __init__(self, engine: GameEngine):
        self._engine = engine

    def login(self) -> None:
        pass  # no-op for local

    def send_move(self, source: Position, target: Position) -> None:
        self._engine.request_move(source, target)

    def send_jump(self, pos: Position) -> None:
        self._engine.request_jump(pos)

    def get_board(self) -> Board:
        return self._engine.board

    def get_state(self) -> GameState:
        return self._engine.state

    def advance_time(self, ms: int) -> None:
        self._engine.advance_time(ms)

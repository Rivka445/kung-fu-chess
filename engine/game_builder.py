from dataclasses import dataclass
from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine
from engine.game_engine import GameEngine
from input.controller import Controller
from events.base import GameEventListener


@dataclass(frozen=True)
class GameApplication:
    engine: GameEngine
    controller: Controller


def build_game(board: Board, listeners: list[GameEventListener] | None = None) -> GameApplication:
    engine = GameEngine(board, RuleEngine())
    for listener in (listeners or []):
        engine.add_listener(listener)
    return GameApplication(engine=engine, controller=Controller(engine))


class GameBuilder:
    """Kept for script_runner compatibility."""
    def __init__(self):
        self._board = Board()
        self._listeners: list[GameEventListener] = []

    def with_row(self, line: str) -> "GameBuilder":
        self._board.add_parsed_row(parse_row(line, self._board.expected_cols))
        return self

    def with_listener(self, listener: GameEventListener) -> "GameBuilder":
        self._listeners.append(listener)
        return self

    def build(self) -> GameApplication:
        return build_game(self._board, self._listeners)

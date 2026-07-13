from dataclasses import dataclass
from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine
from engine.game_engine import GameEngine
from input.controller import Controller
from events.base import GameEventListener


@dataclass(frozen=True)
class GameApplication:
    """A fully assembled game — holds the engine and the controller."""
    engine: GameEngine
    controller: Controller


# ---- Factory Function ----

def build_game(board: Board, listeners: list[GameEventListener] | None = None) -> GameApplication:
    """
    Build a complete GameApplication from a pre-constructed board.
    Wires together the engine, rule engine, controller, and any listeners.
    """
    engine = GameEngine(board, RuleEngine())
    for listener in (listeners or []):
        engine.add_listener(listener)
    return GameApplication(engine=engine, controller=Controller(engine))


# ---- Builder (for script-based construction) ----

class GameBuilder:
    """
    Fluent builder for constructing a game row by row from a text script.
    Follows the Builder Pattern — allows incremental setup before calling build().
    """

    def __init__(self):
        self._board = Board()
        self._listeners: list[GameEventListener] = []

    def with_row(self, line: str) -> "GameBuilder":
        """Parse and append a board row. Returns self for method chaining."""
        self._board.add_parsed_row(parse_row(line, self._board.expected_cols))
        return self

    def with_listener(self, listener: GameEventListener) -> "GameBuilder":
        """Register an event listener. Returns self for method chaining."""
        self._listeners.append(listener)
        return self

    def build(self) -> GameApplication:
        """Finalize and return the assembled GameApplication."""
        return build_game(self._board, self._listeners)

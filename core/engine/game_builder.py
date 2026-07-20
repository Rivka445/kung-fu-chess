from dataclasses import dataclass
from core.model.board import Board
from core.board_io.board_parser import parse_row
from core.rules.rule_engine import RuleEngine
from core.engine.game_engine import GameEngine
from core.input.controller import Controller


@dataclass(frozen=True)
class GameApplication:
    """A fully assembled game — holds the engine and the controller."""
    engine: GameEngine
    controller: Controller


def build_game(board: Board) -> GameApplication:
    """Build a complete GameApplication from a pre-constructed board."""
    engine = GameEngine(board, RuleEngine())
    return GameApplication(engine=engine, controller=Controller(engine))


class GameBuilder:
    """
    Fluent builder for constructing a game row by row from a text script.
    Follows the Builder Pattern — allows incremental setup before calling build().
    """

    def __init__(self):
        self._board = Board()

    def with_row(self, line: str) -> "GameBuilder":
        """Parse and append a board row. Returns self for method chaining."""
        self._board.add_parsed_row(parse_row(line, self._board.expected_cols))
        return self

    def build(self) -> GameApplication:
        """Finalize and return the assembled GameApplication."""
        return build_game(self._board)

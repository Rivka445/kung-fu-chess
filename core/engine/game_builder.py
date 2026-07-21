from dataclasses import dataclass
from core.model.board import Board
from core.board_io.board_parser import parse_row
from core.rules.rule_engine import RuleEngine
from core.engine.game_engine import GameEngine


@dataclass(frozen=True)
class GameApplication:
    """A fully assembled game — holds the engine."""
    engine: GameEngine


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
        engine = GameEngine(self._board, RuleEngine())
        return GameApplication(engine=engine)

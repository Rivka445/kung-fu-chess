from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine
from engine.game_engine import GameEngine
from input.controller import Controller
from events.base import GameEventListener


class GameBuilder:
    def __init__(self):
        self._board = Board()
        self._listeners: list[GameEventListener] = []

    def with_row(self, line: str) -> "GameBuilder":
        self._board.add_parsed_row(parse_row(line, self._board.expected_cols))
        return self

    def with_listener(self, listener: GameEventListener) -> "GameBuilder":
        self._listeners.append(listener)
        return self

    def build(self) -> tuple[GameEngine, Controller]:
        engine = GameEngine(self._board, RuleEngine())
        for listener in self._listeners:
            engine.add_listener(listener)
        return engine, Controller(engine)

import sys
from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine
from engine.game_engine import GameEngine
from input.controller import Controller
from script_test.script_parser import execute
from events.log_listener import LogListener
from constants import CELL_SIZE
from exceptions import BoardParseError
from logger import logger


def run(stream=None):
    if stream is None:
        stream = sys.stdin
    board = Board()
    engine = GameEngine(board, RuleEngine())
    engine.add_listener(LogListener())
    controller = Controller(engine)

    in_board = False
    in_commands = False

    for line in stream:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str == "Board:":
            in_board, in_commands = True, False
            continue
        if line_str == "Commands:":
            in_board, in_commands = False, True
            continue
        if in_board:
            try:
                board.add_parsed_row(parse_row(line_str, board.expected_cols))
            except BoardParseError as e:
                logger.error("board parse error: %s", e)
                code = type(e).__name__.replace("Error", "")
                code = "".join(f"_{c}" if c.isupper() and i > 0 else c for i, c in enumerate(code)).upper()
                print(f"ERROR {code}")
                sys.exit(0)
        elif in_commands:
            execute(line_str, controller, engine, CELL_SIZE)

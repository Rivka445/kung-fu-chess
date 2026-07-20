import sys
from core.engine.game_builder import GameBuilder, GameApplication
from script_test.script_parser import execute
from core.events.log_listener import LogListener
from constants import CELL_SIZE
from exceptions import BoardParseError
from logger import logger


def run(stream=None):
    if stream is None:
        stream = sys.stdin

    builder = GameBuilder()
    app: GameApplication | None = None

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
            app = builder.build()
            LogListener(app.engine.bus)
            continue
        if in_board:
            try:
                builder.with_row(line_str)
            except BoardParseError as e:
                logger.error("board parse error: %s", e)
                code = type(e).__name__.replace("Error", "")
                code = "".join(f"_{c}" if c.isupper() and i > 0 else c for i, c in enumerate(code)).upper()
                print(f"ERROR {code}")
                sys.exit(0)
        elif in_commands:
            execute(line_str, app.controller, app.engine)

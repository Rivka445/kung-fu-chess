import sys
from services.board import ChessBoard
from services.board_parser import parse_row
from services.move_rules import Rules
from controllers.game_controller import Game
from constants import CELL_SIZE
from exceptions import BoardParseError
from logger import logger


def main():
    """Entry point for the Kung Fu Chess engine.
    Reads input from stdin in two sections: 'Board:' defines the initial board layout row by row,
    and 'Commands:' contains a sequence of game commands to execute such as click, wait, jump, and print board."""
    board = ChessBoard()
    rules = Rules()
    game = Game(board, rules)

    in_board_section = False
    in_commands_section = False

    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue

        if line_str == "Board:":
            in_board_section = True
            in_commands_section = False
            continue

        if line_str == "Commands:":
            in_board_section = False
            in_commands_section = True
            continue

        if in_board_section:
            try:
                row = parse_row(line_str, board.expected_cols)
                board.add_parsed_row(row)
            except BoardParseError as e:
                logger.error("board parse error: %s", e)
                print(f"ERROR {e}")
                sys.exit(0)

        elif in_commands_section:
            execute_command(line_str, game, CELL_SIZE)


if __name__ == "__main__":
    main()

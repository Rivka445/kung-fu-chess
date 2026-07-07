import sys
from board import ChessBoard
from board_parser import parse_row
from game import Game
from commands import execute_command
from config import CELL_SIZE

def main():
    board = ChessBoard()
    game = Game(board)

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
            except ValueError as e:
                print(f"ERROR {e}")
                sys.exit(0)
        
        elif in_commands_section:
            execute_command(line_str, game, CELL_SIZE)

if __name__ == "__main__":
    main()
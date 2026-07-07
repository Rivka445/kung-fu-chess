# main.py
import sys
from board import ChessBoard

def main():
    chess_game = ChessBoard()
    in_board_section = False

    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
            
        # Context-switching triggers
        if line_str == "Board:":
            in_board_section = True
            continue
            
        if line_str == "Commands:":
            in_board_section = False
            continue
            
        if line_str == "print board":
            chess_game.print_board()
            continue

        # Append data to the board when within the target block
        if in_board_section:
            chess_game.add_row(line_str)

if __name__ == "__main__":
    main()
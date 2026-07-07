# main.py
import sys
from board import ChessBoard
from game import Game
from commands import execute_command

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
            board.add_row(line_str)
        
        elif in_commands_section:
            execute_command(line_str, game)

if __name__ == "__main__":
    main()
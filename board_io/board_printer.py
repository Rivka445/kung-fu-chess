from model.board import Board


def print_board(board: Board):
    for row in board.matrix:
        print(" ".join(p.to_str() if p is not None else "." for p in row))

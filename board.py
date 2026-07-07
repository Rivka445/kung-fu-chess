# board.py
import sys
from pieces import VALID_PIECE_TYPES, VALID_COLORS

class ChessBoard:
    def __init__(self):
        self.matrix = []
        self.expected_cols = None

    def add_row(self, line_str: str):
        tokens = line_str.split()
        
        if len(tokens) == 0:
            print("ERROR EMPTY_ROW")
            sys.exit(0)

        if self.expected_cols is None:
            self.expected_cols = len(tokens)
        elif len(tokens) != self.expected_cols:
            print("ERROR ROW_WIDTH_MISMATCH")
            sys.exit(0)
            
        for token in tokens:
            if token == ".":
                continue
            
            if len(token) != 2:
                print("ERROR UNKNOWN_TOKEN")
                sys.exit(0)
            
            color = token[0]
            piece_type = token[1]

            if color not in VALID_COLORS or piece_type not in VALID_PIECE_TYPES:
                print("ERROR UNKNOWN_TOKEN")
                sys.exit(0)
  
        self.matrix.append(tokens)


    def is_inside(self, row, col):
        return (
            row >= 0 and
            col >= 0 and
            row < len(self.matrix) and
            col < self.expected_cols
        )

    def get_piece(self, row, col):
        return self.matrix[row][col]
    
    def same_color(self, piece1, piece2):
        return piece1 != "." and piece2 != "." and piece1[0] == piece2[0]

    def target_has_same_color(self, source_row, source_col, target_row, target_col):
        source_piece = self.get_piece(source_row, source_col)
        target_piece = self.get_piece(target_row, target_col)

        return self.same_color(source_piece, target_piece)
    
    def has_blockers(self, source_row, source_col, target_row, target_col):
        row_step = self.get_step(target_row - source_row)
        col_step = self.get_step(target_col - source_col)

        current_row = source_row + row_step
        current_col = source_col + col_step

        while current_row != target_row or current_col != target_col:
            if self.get_piece(current_row, current_col) != ".":
                return True

            current_row += row_step
            current_col += col_step

        return False

    def get_step(self, diff):
        if diff > 0:
            return 1
        if diff < 0:
            return -1
        return 0

    def move_piece(self, source_row, source_col, target_row, target_col):
        piece = self.matrix[source_row][source_col]
        self.matrix[target_row][target_col] = piece
        self.matrix[source_row][source_col] = "."

    def print_board(self):
        for row in self.matrix:
            print(" ".join(row))
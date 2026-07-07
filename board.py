# board.py
import sys
from pieces import VALID_PIECE_TYPES, VALID_COLORS

class ChessBoard:
    def __init__(self):
        self.matrix = []
        self.expected_cols = None

    def add_row(self, line_str: str):
        """
        Parses a single row from the board text section, validates dimensions and tokens.
        """
        tokens = line_str.split()
        
        # Enforce exact rectangular column matching
        if self.expected_cols is None:
            self.expected_cols = len(tokens)
        elif len(tokens) != self.expected_cols:
            print("ERROR ROW_WIDTH_MISMATCH")
            sys.exit(0)
            
        # Validate individual tokens
        for token in tokens:
            if token == ".":
                continue
            
            # Ensure token format is exactly 2 characters (Color + Type)
            if len(token) != 2 or token[0] not in VALID_COLORS or token[1] not in VALID_PIECE_TYPES:
                print("ERROR UNKNOWN_TOKEN")
                sys.exit(0)
                
        self.matrix.append(tokens)

    def print_board(self):
        """
        Prints the current state of the board in canonical text form.
        """
        for row in self.matrix:
            print(" ".join(row))
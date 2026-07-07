from pieces import VALID_PIECE_TYPES, VALID_COLORS

class ChessBoard:
    def __init__(self):
        self.matrix = []
        self.expected_cols = None

    def add_row(self, line_str: str):
        tokens = line_str.split()
        
        if not tokens:
            raise ValueError("EMPTY_ROW")

        if self.expected_cols is None:
            self.expected_cols = len(tokens)
        elif len(tokens) != self.expected_cols:
            raise ValueError("ROW_WIDTH_MISMATCH")
            
        for token in tokens:
            if token == ".":
                continue
            
            if len(token) != 2:
                raise ValueError("UNKNOWN_TOKEN")
            
            color = token[0]
            piece_type = token[1]

            if color not in VALID_COLORS or piece_type not in VALID_PIECE_TYPES:
                raise ValueError("UNKNOWN_TOKEN")
  
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
        path = self.get_path(source_row, source_col, target_row, target_col)
        for row, col in path[:-1]:
            if self.get_piece(row, col) != ".":
                return True
        return False

    def get_step(self, diff):
        if diff > 0:
            return 1
        if diff < 0:
            return -1
        return 0

    def get_path(self, source_row, source_col, target_row, target_col):
        row_step = self.get_step(target_row - source_row)
        col_step = self.get_step(target_col - source_col)
        path = []
        current_row = source_row + row_step
        current_col = source_col + col_step
        while True:
            path.append((current_row, current_col))
            if current_row == target_row and current_col == target_col:
                break
            current_row += row_step
            current_col += col_step
        return path

    def is_on_path(self, source_row, source_col, target_row, target_col, check_row, check_col):
        return (check_row, check_col) in self.get_path(source_row, source_col, target_row, target_col)

    def promote_pawn(self, row, col):
        piece = self.matrix[row][col]
        if piece == "." or piece[1] != "P":
            return
        last_row = 0 if piece[0] == "w" else len(self.matrix) - 1
        if row == last_row:
            self.matrix[row][col] = piece[0] + "Q"

    def remove_piece(self, row, col):
        self.matrix[row][col] = "."

    def move_piece(self, source_row, source_col, target_row, target_col):
        piece = self.matrix[source_row][source_col]
        self.matrix[target_row][target_col] = piece
        self.matrix[source_row][source_col] = "."

    def print_board(self):
        for row in self.matrix:
            print(" ".join(row))
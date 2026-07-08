from models.piece import Piece, PieceType, Color
from models.position import Position, to_chess_notation
from logger import logger


class ChessBoard:
    """Represents the physical chess board as a 2D matrix of pieces.
    Responsible for storing piece positions and performing low-level board operations."""

    def __init__(self):
        """Initializes an empty board with no rows and no defined column count."""
        self.matrix = []
        self.expected_cols = None

    def add_parsed_row(self, row: list):
        """Adds a parsed row of pieces to the board.
        The first row added determines the expected number of columns for all subsequent rows."""
        if self.expected_cols is None:
            self.expected_cols = len(row)
        self.matrix.append(row)
        logger.debug("loaded board row %d: %s", len(self.matrix), [p.to_str() if p else "." for p in row])

    def is_inside(self, pos: Position) -> bool:
        """Returns True if the given position is within the bounds of the board.
        Returns False if the board has no rows yet or if the position is out of range."""
        if self.expected_cols is None:
            return False
        return 0 <= pos.row < len(self.matrix) and 0 <= pos.col < self.expected_cols

    def get_piece(self, pos: Position):
        """Returns the piece at the given position, or None if the cell is empty."""
        return self.matrix[pos.row][pos.col]

    def set_piece(self, pos: Position, piece):
        """Places a piece at the given position. Pass None to clear the cell."""
        self.matrix[pos.row][pos.col] = piece

    def same_color(self, p1, p2) -> bool:
        """Returns True if both pieces exist and share the same color.
        Returns False if either piece is None."""
        return p1 is not None and p2 is not None and p1.same_color(p2)

    def has_blockers(self, source: Position, target: Position) -> bool:
        """Returns True if any piece occupies a cell along the path from source to target, excluding the target itself.
        Used to enforce the rule that rooks, bishops, and queens cannot pass through other pieces."""
        for pos in self.path(source, target)[:-1]:
            if self.get_piece(pos) is not None:
                return True
        return False

    def _step(self, diff):
        """Returns the unit step direction for a single axis: 1, -1, or 0 depending on the sign of diff."""
        return 1 if diff > 0 else (-1 if diff < 0 else 0)

    def path(self, source: Position, target: Position):
        """Returns a list of all positions between source and target, including the target but excluding the source.
        Moves one step at a time in the correct direction along each axis."""
        row_step = self._step(target.row - source.row)
        col_step = self._step(target.col - source.col)
        path = []
        r, c = source.row + row_step, source.col + col_step
        while True:
            path.append(Position(r, c))
            if r == target.row and c == target.col:
                break
            r += row_step
            c += col_step
        return path

    def move_piece(self, source: Position, target: Position):
        """Moves the piece from source to target and clears the source cell."""
        piece = self.get_piece(source)
        self.set_piece(target, piece)
        self.set_piece(source, None)

    def remove_piece(self, pos: Position):
        """Removes the piece at the given position by setting the cell to None."""
        self.set_piece(pos, None)

    def promote_pawn(self, pos: Position):
        """Promotes a pawn to a queen if it has reached the last row for its color.
        White pawns promote at row 0, black pawns promote at the last row of the board."""
        piece = self.get_piece(pos)
        if piece is None or not piece.is_pawn:
            return
        last_row = 0 if piece.color == Color.WHITE else len(self.matrix) - 1
        if pos.row == last_row:
            self.set_piece(pos, Piece(piece.color, PieceType.QUEEN))
            logger.info("pawn promoted to queen at %s", pos)

    def print_board(self):
        """Prints the board to stdout with chess notation labels.
        Row numbers are displayed on the left and column letters are displayed at the bottom."""
        board_rows = len(self.matrix)
        for r, row in enumerate(self.matrix):
            row_num = board_rows - r
            print(f"{row_num} " + " ".join(p.to_str() if p is not None else "." for p in row))
        print("  " + " ".join(chr(ord('a') + c) for c in range(self.expected_cols)))

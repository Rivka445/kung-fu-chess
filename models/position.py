from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """Immutable representation of a cell on the board using zero-based row and column indices.
    Row 0 is the top of the board, col 0 is the leftmost column."""
    row: int
    col: int

    def __iter__(self):
        """Allows unpacking a Position directly, e.g. row, col = Position(2, 3)."""
        yield self.row
        yield self.col


def to_chess_notation(pos: Position, board_rows: int) -> str:
    """Converts an internal Position to standard chess notation.
    For example, Position(0, 0) on an 8-row board becomes 'a8'.
    Columns map to letters starting from 'a', and rows are flipped so that row 0 maps to the highest number."""
    col_char = chr(ord('a') + pos.col)
    row_num = board_rows - pos.row
    return f"{col_char}{row_num}"


def from_chess_notation(notation: str, board_rows: int) -> Position:
    """Converts standard chess notation to an internal Position.
    For example, 'a8' on an 8-row board becomes Position(0, 0).
    Supports any board size as long as board_rows is provided correctly."""
    col = ord(notation[0]) - ord('a')
    row = board_rows - int(notation[1])
    return Position(row, col)

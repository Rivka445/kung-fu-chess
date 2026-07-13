from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """
    Immutable (row, col) coordinate on the board.
    frozen=True allows positions to be used as dict keys and set members.
    """
    row: int
    col: int

    def __iter__(self):
        """Allow unpacking: row, col = position."""
        yield self.row
        yield self.col


# ---- Notation helpers ----

def to_chess_notation(pos: Position, board_rows: int) -> str:
    """Convert a Position to standard chess notation (e.g. Position(6,4) -> 'e2')."""
    return f"{chr(ord('a') + pos.col)}{board_rows - pos.row}"


def from_chess_notation(notation: str, board_rows: int) -> Position:
    """Convert standard chess notation to a Position (e.g. 'e2' -> Position(6,4))."""
    return Position(board_rows - int(notation[1]), ord(notation[0]) - ord('a'))

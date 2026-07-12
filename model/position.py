from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def __iter__(self):
        yield self.row
        yield self.col


def to_chess_notation(pos: Position, board_rows: int) -> str:
    return f"{chr(ord('a') + pos.col)}{board_rows - pos.row}"


def from_chess_notation(notation: str, board_rows: int) -> Position:
    return Position(board_rows - int(notation[1]), ord(notation[0]) - ord('a'))

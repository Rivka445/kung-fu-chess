from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def __iter__(self):
        yield self.row
        yield self.col


def to_chess_notation(pos: Position, board_rows: int) -> str:
    col_char = chr(ord('a') + pos.col)
    row_num = board_rows - pos.row
    return f"{col_char}{row_num}"


def from_chess_notation(notation: str, board_rows: int) -> Position:
    col = ord(notation[0]) - ord('a')
    row = board_rows - int(notation[1])
    return Position(row, col)

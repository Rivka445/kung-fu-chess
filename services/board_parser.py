from models.piece import Piece, VALID_COLORS, VALID_PIECE_TYPES
from exceptions import EmptyRowError, RowWidthMismatchError, UnknownTokenError


def parse_row(line_str: str, expected_cols: int = None):
    """Parses a single line of text into a list of Piece objects and None values.
    Each token in the line represents one cell: '.' means empty, and a two-character string like 'wR' means a piece.
    Raises ValueError with a descriptive code if the row is empty, has the wrong number of columns, or contains an unknown token."""
    tokens = line_str.split()

    if not tokens:
        raise EmptyRowError()

    if expected_cols is not None and len(tokens) != expected_cols:
        raise RowWidthMismatchError(expected_cols, len(tokens))

    row = []
    for token in tokens:
        if token == ".":
            row.append(None)
            continue
        if len(token) != 2 or token[0] not in VALID_COLORS or token[1] not in VALID_PIECE_TYPES:
            raise UnknownTokenError(token)
        row.append(Piece.from_str(token))

    return row

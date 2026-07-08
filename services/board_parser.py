from models.piece import Piece, VALID_COLORS, VALID_PIECE_TYPES


def parse_row(line_str: str, expected_cols: int = None):
    tokens = line_str.split()

    if not tokens:
        raise ValueError("EMPTY_ROW")

    if expected_cols is not None and len(tokens) != expected_cols:
        raise ValueError("ROW_WIDTH_MISMATCH")

    row = []
    for token in tokens:
        if token == ".":
            row.append(None)
            continue
        if len(token) != 2 or token[0] not in VALID_COLORS or token[1] not in VALID_PIECE_TYPES:
            raise ValueError("UNKNOWN_TOKEN")
        row.append(Piece.from_str(token))

    return row

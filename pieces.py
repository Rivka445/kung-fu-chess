VALID_PIECE_TYPES = {'K', 'Q', 'R', 'B', 'N', 'P'}
VALID_COLORS = {'w', 'b'}
BLOCKABLE_PIECES = {'R', 'B', 'Q'}


def king_move(dr, dc):
    return dr <= 1 and dc <= 1


def rook_move(dr, dc):
    return dr == 0 or dc == 0


def bishop_move(dr, dc):
    return dr == dc


def queen_move(dr, dc):
    return rook_move(dr, dc) or bishop_move(dr, dc)


def knight_move(dr, dc):
    return (dr, dc) in {(2, 1), (1, 2)}


MOVE_RULES = {
    "K": king_move,
    "R": rook_move,
    "B": bishop_move,
    "Q": queen_move,
    "N": knight_move,
}


def is_legal_pawn_move(piece, source_row, source_col, target_row, target_col, target_piece):
    color = piece[0]

    row_diff = target_row - source_row
    col_diff = target_col - source_col

    expected_row_diff = -1 if color == "w" else 1

    if row_diff != expected_row_diff:
        return False

    if col_diff == 0:
        return target_piece == "."

    if abs(col_diff) == 1:
        return target_piece != "." and target_piece[0] != color

    return False


def is_legal_move(piece, source_row, source_col, target_row, target_col):
    piece_type = piece[1]

    dr = abs(target_row - source_row)
    dc = abs(target_col - source_col)

    if dr == 0 and dc == 0:
        return False

    rule = MOVE_RULES.get(piece_type)

    if rule is None:
        return False

    return rule(dr, dc)
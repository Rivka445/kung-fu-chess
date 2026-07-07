from piece import Piece, PieceType, Color, BLOCKABLE

BLOCKABLE_PIECES = BLOCKABLE


def _king_move(dr, dc): return dr <= 1 and dc <= 1
def _rook_move(dr, dc): return dr == 0 or dc == 0
def _bishop_move(dr, dc): return dr == dc
def _queen_move(dr, dc): return _rook_move(dr, dc) or _bishop_move(dr, dc)
def _knight_move(dr, dc): return (dr, dc) in {(2, 1), (1, 2)}


_MOVE_RULES = {
    PieceType.KING: _king_move,
    PieceType.ROOK: _rook_move,
    PieceType.BISHOP: _bishop_move,
    PieceType.QUEEN: _queen_move,
    PieceType.KNIGHT: _knight_move,
}


def is_legal_move(piece: Piece, source, target) -> bool:
    dr = abs(target.row - source.row)
    dc = abs(target.col - source.col)
    if dr == 0 and dc == 0:
        return False
    rule = _MOVE_RULES.get(piece.type)
    return rule(dr, dc) if rule else False


def is_legal_pawn_move(piece: Piece, source, target, target_piece, board_rows=8) -> bool:
    expected_dir = -1 if piece.color == Color.WHITE else 1
    start_row = board_rows - 1 if piece.color == Color.WHITE else 0
    row_diff = target.row - source.row
    col_diff = target.col - source.col
    if col_diff == 0:
        if row_diff == expected_dir:
            return target_piece is None
        if row_diff == 2 * expected_dir and source.row == start_row:
            return target_piece is None
        return False
    if abs(col_diff) == 1 and row_diff == expected_dir:
        return target_piece is not None and not piece.same_color(target_piece)
    return False

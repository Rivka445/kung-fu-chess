from model.piece import Piece, Color
from model.position import Position
from rules.piece_rules import MOVE_STRATEGIES


class RuleEngine:
    def is_legal(self, piece: Piece, source: Position, target: Position, board) -> bool:
        if source == target:
            return False
        if piece.is_pawn:
            return self._pawn(piece, source, target, board)
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        strategy = MOVE_STRATEGIES.get(piece.type)
        if not strategy or not strategy.is_legal(dr, dc):
            return False
        if board.same_color(piece, board.get_piece(target)):
            return False
        if piece.is_blockable and board.has_blockers(source, target):
            return False
        return True

    def _pawn(self, piece: Piece, source: Position, target: Position, board) -> bool:
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = len(board.matrix) - 1 if piece.color == Color.WHITE else 0
        dr = target.row - source.row
        dc = target.col - source.col
        target_piece = board.get_piece(target)
        if dc == 0:
            if dr == direction:
                return target_piece is None
            if dr == 2 * direction and source.row == start_row:
                return target_piece is None and not board.has_blockers(source, target)
            return False
        if abs(dc) == 1 and dr == direction:
            return target_piece is not None and not piece.same_color(target_piece)
        return False

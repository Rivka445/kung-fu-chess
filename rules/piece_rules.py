from abc import ABC, abstractmethod
from model.piece import PieceType, Color


class MoveStrategy(ABC):
    def _available(self, piece, target, board) -> bool:
        return not board.same_color(piece, board.get_piece(target))

    def _clear(self, source, target, board) -> bool:
        return not board.has_blockers(source, target)

    @abstractmethod
    def is_legal(self, piece, source, target, board) -> bool: ...


class KingStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return dr <= 1 and dc <= 1 and self._available(piece, target, board)


class RookStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr == 0 or dc == 0) and self._available(piece, target, board) and self._clear(source, target, board)


class BishopStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return dr == dc and self._available(piece, target, board) and self._clear(source, target, board)


class QueenStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr == 0 or dc == 0 or dr == dc) and self._available(piece, target, board) and self._clear(source, target, board)


class KnightStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr, dc) in {(2, 1), (1, 2)} and self._available(piece, target, board)


class PawnStrategy(MoveStrategy):
    def is_legal(self, piece, source, target, board):
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = len(board.matrix) - 2 if piece.color == Color.WHITE else 1
        dr = target.row - source.row
        dc = target.col - source.col
        target_piece = board.get_piece(target)
        if dc == 0:
            if dr == direction:
                return target_piece is None
            if dr == 2 * direction and source.row == start_row:
                return target_piece is None and self._clear(source, target, board)
            return False
        if abs(dc) == 1 and dr == direction:
            return target_piece is not None and not piece.same_color(target_piece)
        return False


MOVE_STRATEGIES: dict[PieceType, MoveStrategy] = {
    PieceType.KING: KingStrategy(),
    PieceType.ROOK: RookStrategy(),
    PieceType.BISHOP: BishopStrategy(),
    PieceType.QUEEN: QueenStrategy(),
    PieceType.KNIGHT: KnightStrategy(),
    PieceType.PAWN: PawnStrategy(),
}

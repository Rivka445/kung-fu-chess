from abc import ABC, abstractmethod
from models.piece import Piece, PieceType, Color, BLOCKABLE


class MoveStrategy(ABC):
    """Base strategy for validating the shape of a piece's move.
    Receives absolute row and column differences and returns True if the move shape is legal."""
    @abstractmethod
    def is_legal(self, dr: int, dc: int) -> bool: ...


class KingStrategy(MoveStrategy):
    def is_legal(self, dr, dc): return dr <= 1 and dc <= 1

class RookStrategy(MoveStrategy):
    def is_legal(self, dr, dc): return dr == 0 or dc == 0

class BishopStrategy(MoveStrategy):
    def is_legal(self, dr, dc): return dr == dc

class QueenStrategy(MoveStrategy):
    def is_legal(self, dr, dc): return dr == 0 or dc == 0 or dr == dc

class KnightStrategy(MoveStrategy):
    def is_legal(self, dr, dc): return (dr, dc) in {(2, 1), (1, 2)}


# Maps each piece type to its MoveStrategy instance.
# To add a new piece type, create a MoveStrategy subclass and register it here.
_MOVE_RULES: dict[PieceType, MoveStrategy] = {
    PieceType.KING: KingStrategy(),
    PieceType.ROOK: RookStrategy(),
    PieceType.BISHOP: BishopStrategy(),
    PieceType.QUEEN: QueenStrategy(),
    PieceType.KNIGHT: KnightStrategy(),
}


class Rules:
    """Contains all movement validation logic for chess pieces.
    Determines whether a given move is legal based on piece type, direction, distance, and board context."""

    def is_legal_move(self, piece: Piece, source, target) -> bool:
        """Returns True if the move from source to target is legal for the given piece.
        Delegates shape validation to the registered MoveStrategy for the piece type.
        Does not check for blockers or board boundaries — those are handled separately.
        Pawns are not handled here; use is_legal_pawn_move instead."""
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        if dr == 0 and dc == 0:
            return False
        strategy = _MOVE_RULES.get(piece.type)
        return strategy.is_legal(dr, dc) if strategy else False

    def is_legal_pawn_move(self, piece: Piece, source, target, target_piece, board_rows=8, has_blocker=False) -> bool:
        """Returns True if the pawn move from source to target is legal.
        Handles all pawn-specific rules: forward movement, double step from starting row, and diagonal capture.
        White pawns move upward (decreasing row), black pawns move downward (increasing row).
        The has_blocker parameter is used to reject a double step if a piece stands in the way."""
        expected_dir = -1 if piece.color == Color.WHITE else 1
        start_row = board_rows - 1 if piece.color == Color.WHITE else 0
        row_diff = target.row - source.row
        col_diff = target.col - source.col
        if col_diff == 0:
            if row_diff == expected_dir:
                return target_piece is None
            if row_diff == 2 * expected_dir and source.row == start_row:
                return target_piece is None and not has_blocker
            return False
        if abs(col_diff) == 1 and row_diff == expected_dir:
            return target_piece is not None and not piece.same_color(target_piece)
        return False

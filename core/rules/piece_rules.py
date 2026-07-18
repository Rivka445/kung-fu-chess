from abc import ABC, abstractmethod
from core.model.piece import PieceType, Color


# ---- Base Strategy ----

class MoveStrategy(ABC):
    """
    Abstract base for piece movement rules.
    Each piece type has its own concrete strategy.
    Follows the Strategy Pattern — the caller uses is_legal() without knowing the piece type.
    """

    def _available(self, piece, target, board) -> bool:
        """Return True if the target square is empty or occupied by an enemy piece."""
        return not board.same_color(piece, board.get_piece(target))

    def _clear(self, source, target, board) -> bool:
        """Return True if no pieces are blocking the path between source and target."""
        return not board.has_blockers(source, target)

    @abstractmethod
    def is_legal(self, piece, source, target, board) -> bool:
        """Return True if the move from source to target is legal for this piece type."""
        ...


# ---- Concrete Strategies ----

class KingStrategy(MoveStrategy):
    """King moves one square in any direction."""
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return dr <= 1 and dc <= 1 and self._available(piece, target, board)


class RookStrategy(MoveStrategy):
    """Rook moves any number of squares horizontally or vertically, path must be clear."""
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr == 0 or dc == 0) and self._available(piece, target, board) and self._clear(source, target, board)


class BishopStrategy(MoveStrategy):
    """Bishop moves any number of squares diagonally, path must be clear."""
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return dr == dc and self._available(piece, target, board) and self._clear(source, target, board)


class QueenStrategy(MoveStrategy):
    """Queen combines rook and bishop movement, path must be clear."""
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr == 0 or dc == 0 or dr == dc) and self._available(piece, target, board) and self._clear(source, target, board)


class KnightStrategy(MoveStrategy):
    """Knight moves in an L-shape and can jump over other pieces."""
    def is_legal(self, piece, source, target, board):
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        return (dr, dc) in {(2, 1), (1, 2)} and self._available(piece, target, board)


class PawnStrategy(MoveStrategy):
    """
    Pawn movement rules:
    - One square forward if the target is empty.
    - Two squares forward from the starting row if both squares are empty.
    - One square diagonally forward to capture an enemy piece.
    """
    def is_legal(self, piece, source, target, board):
        direction = -1 if piece.color == Color.WHITE else 1          # White moves up (row decreases)
        start_row = len(board.matrix) - 2 if piece.color == Color.WHITE else 1
        dr = target.row - source.row
        dc = target.col - source.col
        target_piece = board.get_piece(target)

        if dc == 0:
            # Forward move — target must be empty
            if dr == direction:
                return target_piece is None
            # Double forward from starting row — both squares must be empty
            if dr == 2 * direction and source.row == start_row:
                return target_piece is None and self._clear(source, target, board)
            return False

        # Diagonal capture — must be an enemy piece on the target
        if abs(dc) == 1 and dr == direction:
            return target_piece is not None and not piece.same_color(target_piece)

        return False


# ---- Strategy Registry ----

# Maps each piece type to its movement strategy instance
MOVE_STRATEGIES: dict[PieceType, MoveStrategy] = {
    PieceType.KING:   KingStrategy(),
    PieceType.ROOK:   RookStrategy(),
    PieceType.BISHOP: BishopStrategy(),
    PieceType.QUEEN:  QueenStrategy(),
    PieceType.KNIGHT: KnightStrategy(),
    PieceType.PAWN:   PawnStrategy(),
}

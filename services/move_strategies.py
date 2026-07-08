from abc import ABC, abstractmethod
from models.piece import PieceType


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
MOVE_STRATEGIES: dict[PieceType, MoveStrategy] = {
    PieceType.KING: KingStrategy(),
    PieceType.ROOK: RookStrategy(),
    PieceType.BISHOP: BishopStrategy(),
    PieceType.QUEEN: QueenStrategy(),
    PieceType.KNIGHT: KnightStrategy(),
}

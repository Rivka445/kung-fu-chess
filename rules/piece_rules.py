from abc import ABC, abstractmethod
from model.piece import PieceType


class MoveStrategy(ABC):
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


MOVE_STRATEGIES: dict[PieceType, MoveStrategy] = {
    PieceType.KING: KingStrategy(),
    PieceType.ROOK: RookStrategy(),
    PieceType.BISHOP: BishopStrategy(),
    PieceType.QUEEN: QueenStrategy(),
    PieceType.KNIGHT: KnightStrategy(),
}

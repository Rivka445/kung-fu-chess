from model.piece import Piece
from model.position import Position
from rules.piece_rules import MOVE_STRATEGIES


class RuleEngine:
    def is_legal(self, piece: Piece | None, source: Position, target: Position, board) -> bool:
        if piece is None:
            return False
        if not board.is_inside(target):
            return False
        if source == target:
            return False
        strategy = MOVE_STRATEGIES.get(piece.type)
        return strategy is not None and strategy.is_legal(piece, source, target, board)

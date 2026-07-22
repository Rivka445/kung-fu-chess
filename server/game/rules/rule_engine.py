from shared.model.piece import Piece
from shared.model.position import Position
from server.game.rules.piece_rules import MOVE_STRATEGIES


class RuleEngine:
    """
    Facade for move legality checks.
    Performs generic pre-checks (valid piece, inside board, non-trivial move)
    before delegating to the piece-specific MoveStrategy.
    """

    def is_legal(self, piece: Piece | None, source: Position, target: Position, board) -> bool:
        """
        Return True if the move from source to target is legal.
        Checks in order:
          1. A piece exists at the source.
          2. The target is inside the board.
          3. The source and target are different squares.
          4. The piece-specific strategy approves the move.
        """
        if piece is None:
            return False
        if not board.is_inside(target):
            return False
        if source == target:
            return False
        strategy = MOVE_STRATEGIES.get(piece.type)
        return strategy is not None and strategy.is_legal(piece, source, target, board)

    def legal_targets(self, piece: Piece, source: Position, board) -> list[Position]:
        """Return every board position the given piece can legally move to from source."""
        targets = []
        for row in range(len(board.matrix)):
            for col in range(board.expected_cols):
                target = Position(row, col)
                if self.is_legal(piece, source, target, board):
                    targets.append(target)
        return targets

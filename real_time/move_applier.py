from model.game_state import GameState, PendingMove, AirbornePiece
from model.position import Position
from events.base import GameEventListener


class MoveApplier:
    def __init__(self, board, listeners: list[GameEventListener]):
        self._board = board
        self._listeners = listeners

    def apply(self, move: PendingMove, simultaneous: set[Position],
              landed: list[AirbornePiece], state: GameState):
        if move.target in simultaneous:
            self._board.remove_piece(move.target)
            for l in self._listeners: l.on_collision(move.target)
            return

        source_piece = self._board.get_piece(move.source)
        target_piece = self._board.get_piece(move.target)
        airborne_here = next((a for a in state.airborne + landed if a.cell == move.target), None)

        if airborne_here and target_piece is not None and not source_piece.same_color(target_piece):
            self._board.remove_piece(move.source)
            for l in self._listeners: l.on_collision(move.target)
            return

        if target_piece is not None and source_piece.same_color(target_piece):
            return

        self._board.move_piece(move.source, move.target)
        for l in self._listeners: l.on_move_applied(move.source, move.target)

        if target_piece is not None and target_piece.is_king:
            for l in self._listeners: l.on_king_captured(move.target)
            state.game_over = True

        piece = self._board.get_piece(move.target)
        if piece is not None and piece.is_pawn:
            self._board.promote_pawn(move.target)
            for l in self._listeners: l.on_pawn_promoted(move.target)

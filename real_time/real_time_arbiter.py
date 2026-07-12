from model.game_state import GameState, PendingMove, AirbornePiece
from model.position import Position
from constants import MOVE_DURATION
from logger import logger


class RealTimeArbiter:
    def __init__(self, board, listeners):
        self.board = board
        self._listeners = listeners

    def advance(self, ms: int, state: GameState):
        state.current_time += ms
        ready, landed = self._partition(state)
        for a in landed:
            state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION
        simultaneous = {
            m.target for m in ready
            if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1
        }
        for move in sorted(ready, key=lambda m: m.arrival):
            self._apply(move, simultaneous, landed, state)

    def launch(self, pos: Position, state: GameState):
        state.airborne.append(AirbornePiece(pos, state.current_time + MOVE_DURATION))
        logger.info("jump: %s launched from %s", self.board.get_piece(pos).to_str(), pos)

    def _partition(self, state: GameState):
        ready = [m for m in state.pending_moves if m.arrival <= state.current_time]
        state.pending_moves = [m for m in state.pending_moves if m.arrival > state.current_time]
        landed = [a for a in state.airborne if a.landing_time <= state.current_time]
        state.airborne = [a for a in state.airborne if a.landing_time > state.current_time]
        return ready, landed

    def _apply(self, move: PendingMove, simultaneous: set, landed: list, state: GameState):
        if move.target in simultaneous:
            self.board.remove_piece(move.target)
            for l in self._listeners: l.on_collision(move.target)
            return
        source_piece = self.board.get_piece(move.source)
        target_piece = self.board.get_piece(move.target)
        airborne_here = next((a for a in state.airborne + landed if a.cell == move.target), None)
        if airborne_here and target_piece is not None and not source_piece.same_color(target_piece):
            self.board.remove_piece(move.source)
            for l in self._listeners: l.on_collision(move.target)
            return
        if target_piece is not None and source_piece.same_color(target_piece):
            return
        self.board.move_piece(move.source, move.target)
        for l in self._listeners: l.on_move_applied(move.source, move.target)
        if target_piece is not None and target_piece.is_king:
            for l in self._listeners: l.on_king_captured(move.target)
            state.game_over = True
        piece = self.board.get_piece(move.target)
        if piece is not None and piece.is_pawn:
            self.board.promote_pawn(move.target)
            for l in self._listeners: l.on_pawn_promoted(move.target)
        state.cooldowns[move.target] = move.arrival + MOVE_DURATION

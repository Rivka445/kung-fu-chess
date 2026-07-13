from collections import defaultdict
from model.game_state import GameState, AirbornePiece, PendingMove
from model.position import Position
from real_time.collision_resolver import CollisionResolver
from constants import MOVE_DURATION
from logger import logger


class RealTimeArbiter:
    def __init__(self, board, listeners):
        self._board = board
        self._listeners = listeners
        self._collision = CollisionResolver()

    def _partition(self, state: GameState) -> tuple[list[PendingMove], list[AirbornePiece]]:
        ready = [m for m in state.pending_moves if m.arrival <= state.current_time]
        state.pending_moves = [m for m in state.pending_moves if m.arrival > state.current_time]
        landed = [a for a in state.airborne if a.landing_time <= state.current_time]
        state.airborne = [a for a in state.airborne if a.landing_time > state.current_time]
        return ready, landed

    def _apply(self, move: PendingMove, simultaneous: set[Position],
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

    def advance(self, ms: int, state: GameState):
        state.current_time += ms
        ready, landed = self._partition(state)
        for a in landed:
            state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION

        ready = self._collision.resolve_head_on(ready)

        by_arrival: dict[int, list[PendingMove]] = defaultdict(list)
        for move in ready:
            by_arrival[move.arrival].append(move)

        for arrival_time in sorted(by_arrival):
            group = by_arrival[arrival_time]
            simultaneous = self._collision.find_simultaneous(group)
            for move in group:
                self._apply(move, simultaneous, landed, state)

    def launch(self, pos: Position, state: GameState):
        state.airborne.append(AirbornePiece(pos, state.current_time + MOVE_DURATION))
        logger.info("jump: %s launched from %s", self._board.get_piece(pos).to_str(), pos)

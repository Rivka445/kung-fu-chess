from collections import defaultdict
from model.game_state import GameState, AirbornePiece, PendingMove
from model.position import Position
from real_time.collision_resolver import CollisionResolver
from constants import MOVE_DURATION
from logger import logger


class RealTimeArbiter:
    """
    Executes real-time game logic as time advances.
    Responsible for:
      - Partitioning pending moves and airborne pieces by time
      - Resolving collisions (head-on and simultaneous)
      - Applying moves to the board
      - Notifying listeners of game events (move, capture, promotion, collision)
    """

    def __init__(self, board, listeners):
        self._board = board
        self._listeners = listeners
        self._collision = CollisionResolver()

    # ---- Internal Helpers ----

    def _partition(self, state: GameState) -> tuple[list[PendingMove], list[AirbornePiece]]:
        """
        Separate moves and airborne pieces into 'ready' (time has come) and 'still waiting'.
        Updates state in-place by removing the ready items from their respective lists.
        """
        ready = [m for m in state.pending_moves if m.arrival <= state.current_time]
        state.pending_moves = [m for m in state.pending_moves if m.arrival > state.current_time]

        landed = [a for a in state.airborne if a.landing_time <= state.current_time]
        state.airborne = [a for a in state.airborne if a.landing_time > state.current_time]

        return ready, landed

    def _apply(self, move: PendingMove, simultaneous: set[Position],
               landed: list[AirbornePiece], state: GameState):
        """
        Apply a single move to the board, handling all collision and capture scenarios.
        Cases handled in priority order:
          1. Simultaneous arrival — two pieces reached the same square at the same time.
          2. Airborne collision — piece lands on a square occupied by an enemy in mid-air.
          3. Friendly piece at target — move is blocked, do nothing.
          4. Normal move — move the piece, check for king capture and pawn promotion.
        """
        # Case 1: another piece arrived at the same target at the same time
        if move.target in simultaneous:
            self._board.remove_piece(move.target)
            for l in self._listeners: l.on_collision(move.target)
            return

        source_piece = self._board.get_piece(move.source)
        target_piece = self._board.get_piece(move.target)
        airborne_here = next((a for a in state.airborne + landed if a.cell == move.target), None)

        # Case 2: enemy piece is landing on the target square — both pieces are removed
        if airborne_here and target_piece is not None and not source_piece.same_color(target_piece):
            self._board.remove_piece(move.source)
            for l in self._listeners: l.on_collision(move.target)
            return

        # Case 3: friendly piece is at the target — move is blocked
        if target_piece is not None and source_piece.same_color(target_piece):
            return

        # Case 4: normal move — execute and check for special outcomes
        self._board.move_piece(move.source, move.target)
        for l in self._listeners: l.on_move_applied(move.source, move.target)

        # Check if the captured piece was a king
        if target_piece is not None and target_piece.is_king:
            for l in self._listeners: l.on_king_captured(move.target)
            state.game_over = True

        # Check if a pawn reached the last row and should be promoted
        piece = self._board.get_piece(move.target)
        if piece is not None and piece.is_pawn:
            self._board.promote_pawn(move.target)
            for l in self._listeners: l.on_pawn_promoted(move.target)

    # ---- Public Interface ----

    def advance(self, ms: int, state: GameState):
        """
        Advance the game clock by ms milliseconds and process all due moves.
        Steps:
          1. Advance current_time.
          2. Partition ready moves and landed pieces.
          3. Assign cooldowns to pieces that just landed.
          4. Resolve head-on collisions before applying any moves.
          5. Apply moves in chronological order, resolving simultaneous arrivals per group.
        """
        state.current_time += ms
        ready, landed = self._partition(state)

        # Assign cooldown to each piece that just finished landing
        for a in landed:
            state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION

        # Remove one side of each head-on collision before processing
        ready = self._collision.resolve_head_on(ready)

        # Group remaining moves by arrival time to process them in order
        by_arrival: dict[int, list[PendingMove]] = defaultdict(list)
        for move in ready:
            by_arrival[move.arrival].append(move)

        for arrival_time in sorted(by_arrival):
            group = by_arrival[arrival_time]
            simultaneous = self._collision.find_simultaneous(group)
            for move in group:
                self._apply(move, simultaneous, landed, state)

    def launch(self, pos: Position, state: GameState):
        """
        Launch a piece into the air from the given position.
        The piece will land after MOVE_DURATION milliseconds.
        """
        state.airborne.append(AirbornePiece(pos, state.current_time + MOVE_DURATION))
        logger.info("jump: %s launched from %s", self._board.get_piece(pos).to_str(), pos)

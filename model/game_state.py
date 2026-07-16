from dataclasses import dataclass, field
from model.position import Position
from model.piece_status import PieceStatus, IdleStatus, InFlightStatus, OnCooldownStatus


# ---- Value Objects ----

@dataclass(frozen=True)
class PendingMove:
    """
    A move that has been submitted but not yet executed.
    Immutable — created once and never modified.
    """
    source: Position   # Where the piece is moving from
    target: Position   # Where the piece is moving to
    arrival: int       # Timestamp (ms) when the piece will reach the target
    seq: int = 0       # Submission order — used to resolve conflicts between simultaneous moves


@dataclass(frozen=True)
class AirbornePiece:
    """
    A piece that has been launched (jumped) and is currently landing.
    Immutable — created once and never modified.
    """
    cell: Position      # The cell where the piece is landing
    landing_time: int   # Timestamp (ms) when the landing completes


# ---- Game State ----

@dataclass
class GameState:
    """
    A snapshot of the real-time game state.
    Mutable — updated continuously as time advances.
    """
    current_time: int = 0                                              # Current game clock in milliseconds
    pending_moves: list[PendingMove] = field(default_factory=list)    # Moves in transit (not yet arrived)
    airborne: list[AirbornePiece] = field(default_factory=list)       # Pieces currently landing
    cooldowns: dict[Position, int] = field(default_factory=dict)      # Maps position -> cooldown expiry time
    game_over: bool = False                                            # True once a king has been captured
    _seq: int = field(default=0, compare=False, repr=False)           # Internal counter for move sequencing

    def next_seq(self) -> int:
        """Return the next unique sequence number for a newly submitted move."""
        self._seq += 1
        return self._seq

    def get_status(self, pos: Position) -> PieceStatus:
        """
        Return the current status of the piece at the given position.
        Priority: in-flight (pending) > in-flight (airborne) > cooldown > idle.
        """
        # Piece has an active move queued — it already left this square
        if any(m.source == pos for m in self.pending_moves):
            return InFlightStatus()

        # Piece is in the process of landing on this square
        if any(a.cell == pos for a in self.airborne):
            return InFlightStatus()

        # Piece recently moved and is still on cooldown
        cooldown_until = self.cooldowns.get(pos, 0)
        if cooldown_until > self.current_time:
            return OnCooldownStatus(cooldown_until)

        return IdleStatus()

    def cleanup_cooldowns(self):
        """Remove expired cooldown entries to prevent unbounded memory growth."""
        self.cooldowns = {pos: t for pos, t in self.cooldowns.items() if t > self.current_time}

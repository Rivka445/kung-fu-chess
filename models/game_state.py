from dataclasses import dataclass, field
from models.position import Position


@dataclass(frozen=True)
class PendingMove:
    """Represents a move that has been requested but has not yet arrived at its destination.
    Stores the source and target positions along with the time the piece is expected to arrive."""
    source: Position
    target: Position
    arrival: int


@dataclass(frozen=True)
class AirbornePiece:
    """Represents a piece that has jumped into the air and has not yet landed.
    Stores the cell it jumped from and the time it is expected to land."""
    cell: Position
    landing_time: int


@dataclass
class GameState:
    """Holds the full runtime state of the game at any given moment.
    This includes the game clock, selected cell, all active moves, airborne pieces, cooldowns, and game over flag."""
    current_time: int = 0
    selected: Position = None
    pending_moves: list = field(default_factory=list)
    airborne: list = field(default_factory=list)
    cooldowns: dict = field(default_factory=dict)
    game_over: bool = False

    def is_busy(self, pos: Position) -> bool:
        """Returns True if the given position is currently unavailable for a new move.
        A position is busy if its piece is already moving, is airborne, or is still in a cooldown period after a recent arrival."""
        return (
            any(m.source == pos for m in self.pending_moves) or
            any(a.cell == pos for a in self.airborne) or
            self.cooldowns.get(pos, 0) > self.current_time
        )

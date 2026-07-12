from dataclasses import dataclass, field
from model.position import Position


@dataclass(frozen=True)
class PendingMove:
    source: Position
    target: Position
    arrival: int


@dataclass(frozen=True)
class AirbornePiece:
    cell: Position
    landing_time: int


@dataclass
class GameState:
    current_time: int = 0
    selected: Position = None
    pending_moves: list = field(default_factory=list)
    airborne: list = field(default_factory=list)
    cooldowns: dict = field(default_factory=dict)
    game_over: bool = False

    def is_busy(self, pos: Position) -> bool:
        return (
            any(m.source == pos for m in self.pending_moves) or
            any(a.cell == pos for a in self.airborne) or
            self.cooldowns.get(pos, 0) > self.current_time
        )

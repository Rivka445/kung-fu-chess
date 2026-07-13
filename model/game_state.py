from dataclasses import dataclass, field
from model.position import Position
from model.piece_status import PieceStatus, IdleStatus, InFlightStatus, OnCooldownStatus


@dataclass(frozen=True)
class PendingMove:
    source: Position
    target: Position
    arrival: int
    seq: int = 0


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
    _seq: int = field(default=0, compare=False, repr=False)

    def next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def get_status(self, pos: Position) -> PieceStatus:
        if any(m.source == pos for m in self.pending_moves):
            return InFlightStatus()
        if any(a.cell == pos for a in self.airborne):
            return InFlightStatus()
        cooldown_until = self.cooldowns.get(pos, 0)
        if cooldown_until > self.current_time:
            return OnCooldownStatus(cooldown_until)
        return IdleStatus()

    def is_busy(self, pos: Position) -> bool:
        return not self.get_status(pos).can_act()

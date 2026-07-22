from dataclasses import dataclass
from shared.model.position import Position
from shared.model.piece import Piece, Color


# ── Events ────────────────────────────────────────────────────────────────────

@dataclass
class MoveApplied:
    source: Position
    target: Position

@dataclass
class Capture:
    captured_piece: Piece
    capturing_color: Color

@dataclass
class KingCaptured:
    pos: Position

@dataclass
class PawnPromoted:
    pos: Position

@dataclass
class Collision:
    pos: Position

@dataclass
class GameStarted: pass

@dataclass
class GameOver: pass


# ── Bus ───────────────────────────────────────────────────────────────────────

class EventBus:
    def __init__(self):
        self._subscribers: dict[type, list] = {}

    def subscribe(self, event_type: type, handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event) -> None:
        for handler in self._subscribers.get(type(event), []):
            handler(event)

from abc import ABC
from model.position import Position


class GameEventListener(ABC):
    """
    Observer interface for game events.
    Implement any subset of methods to react to events fired by RealTimeArbiter.
    Follows the Observer Pattern — the arbiter notifies all registered listeners
    without knowing their concrete implementations.
    """

    def on_move_applied(self, source: Position, target: Position): ...
    """Called when a piece successfully moves from source to target."""

    def on_capture(self, captured_piece, capturing_color): ...
    """Called when a piece is captured (before the board is updated)."""

    def on_king_captured(self, pos: Position): ...
    """Called when a king is captured — signals game over."""

    def on_pawn_promoted(self, pos: Position): ...
    """Called when a pawn is promoted to a queen."""

    def on_collision(self, pos: Position): ...
    """Called when a collision occurs and one or more pieces are removed."""

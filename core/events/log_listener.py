from core.events.base import GameEventListener
from logger import logger


class LogListener(GameEventListener):
    """
    Concrete Observer that logs every game event.
    Useful for debugging and producing a human-readable game transcript.
    """

    def on_move_applied(self, source, target):
        logger.info("moved: %s → %s", source, target)

    def on_king_captured(self, pos):
        logger.warning("king captured at %s — game over", pos)

    def on_pawn_promoted(self, pos):
        logger.info("pawn promoted at %s", pos)

    def on_collision(self, pos):
        logger.info("collision at %s — pieces removed", pos)

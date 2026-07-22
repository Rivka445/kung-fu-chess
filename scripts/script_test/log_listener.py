from shared.events.event_bus import EventBus, MoveApplied, KingCaptured, PawnPromoted, Collision
from shared.helpers.logger import logger


class LogListener:
    def __init__(self, bus: EventBus):
        bus.subscribe(MoveApplied,   lambda e: logger.info("moved: %s → %s", e.source, e.target))
        bus.subscribe(KingCaptured,  lambda e: logger.warning("king captured at %s — game over", e.pos))
        bus.subscribe(PawnPromoted,  lambda e: logger.info("pawn promoted at %s", e.pos))
        bus.subscribe(Collision,     lambda e: logger.info("collision at %s — pieces removed", e.pos))

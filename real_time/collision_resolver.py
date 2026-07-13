from model.game_state import PendingMove
from model.position import Position


class CollisionResolver:
    def resolve_head_on(self, ready: list[PendingMove]) -> list[PendingMove]:
        """Remove the later-queued move from each head-on pair (A->B and B->A, same arrival)."""
        cancelled = set()
        for m in ready:
            for o in ready:
                if (o is not m
                        and o.source == m.target and o.target == m.source
                        and o.arrival == m.arrival
                        and id(o) not in cancelled):
                    loser = o if m.seq < o.seq else m
                    cancelled.add(id(loser))
        return [m for m in ready if id(m) not in cancelled]

    def find_simultaneous(self, ready: list[PendingMove]) -> set[Position]:
        """Return target positions where multiple pieces arrive at the same time."""
        return {
            m.target for m in ready
            if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1
        }

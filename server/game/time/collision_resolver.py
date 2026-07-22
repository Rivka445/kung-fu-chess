from collections import defaultdict
from shared.model.game_state import PendingMove
from shared.model.position import Position
from shared.helpers.logger import logger


# ---- Helpers ----

def _group_by_target(moves: list[PendingMove]) -> dict:
    """Group moves by (arrival, target) — O(M).
    Used to detect multiple pieces arriving at the same square at the same time."""
    groups = defaultdict(list)
    for move in moves:
        groups[(move.arrival, move.target)].append(move)
    return groups


def _edge_key(move: PendingMove) -> tuple:
    """Produce a symmetric key for a potential head-on pair.
    A->B and B->A at the same arrival time will produce the same key,
    allowing them to be grouped together for conflict detection."""
    endpoints = sorted((move.source, move.target), key=lambda p: (p.row, p.col))
    return move.arrival, endpoints[0], endpoints[1]


# ---- Collision Resolver ----

class CollisionResolver:
    """
    Detects and resolves two types of real-time collisions:
      1. Head-on: two pieces swap squares at the same time (A->B and B->A).
      2. Simultaneous: two pieces arrive at the same square at the same time.
    Does not modify the board — only filters and identifies problematic moves.
    """

    def resolve_head_on(self, ready: list[PendingMove]) -> list[PendingMove]:
        """
        Remove the later-queued move from each head-on pair — O(M).
        When two pieces try to swap squares simultaneously, the one with the
        higher seq number (submitted later) is cancelled.
        """
        # Group moves by their symmetric edge key to find potential head-on pairs
        edges: dict[tuple, list[PendingMove]] = defaultdict(list)
        for move in ready:
            edges[_edge_key(move)].append(move)

        cancelled = set()
        for pair in edges.values():
            # A true head-on: exactly 2 moves where each source is the other's target
            if len(pair) == 2 and pair[0].source == pair[1].target:
                loser = max(pair, key=lambda m: m.seq)  # Higher seq = submitted later = loses
                cancelled.add(id(loser))
                logger.info("collision (head-on): %s ↔ %s, cancelled %s → %s",
                            pair[0].source, pair[0].target, loser.source, loser.target)

        return [m for m in ready if id(m) not in cancelled]

    def find_simultaneous(self, ready: list[PendingMove]) -> set[Position]:
        """
        Return the set of target squares where multiple pieces arrive at the same time — O(M).
        The caller (RealTimeArbiter) uses this to handle the collision during move application.
        """
        groups = _group_by_target(ready)
        return {target for (_, target), moves in groups.items() if len(moves) > 1}

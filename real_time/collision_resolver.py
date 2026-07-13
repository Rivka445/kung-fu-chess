from collections import defaultdict
from model.game_state import PendingMove
from model.position import Position


def _group_by_target(moves: list[PendingMove]) -> dict:
    """Group moves by (arrival, target) — O(M)."""
    groups = defaultdict(list)
    for move in moves:
        groups[(move.arrival, move.target)].append(move)
    return groups


def _edge_key(move: PendingMove) -> tuple:
    """Symmetric key for a head-on pair: same key for A->B and B->A at same arrival."""
    endpoints = sorted((move.source, move.target), key=lambda p: (p.row, p.col))
    return move.arrival, endpoints[0], endpoints[1]


class CollisionResolver:
    def resolve_head_on(self, ready: list[PendingMove]) -> list[PendingMove]:
        """Remove the later-queued move from each head-on pair — O(M)."""
        edges: dict[tuple, list[PendingMove]] = defaultdict(list)
        for move in ready:
            edges[_edge_key(move)].append(move)

        cancelled = set()
        for pair in edges.values():
            if len(pair) == 2 and pair[0].source == pair[1].target:
                loser = max(pair, key=lambda m: m.seq)
                cancelled.add(id(loser))

        return [m for m in ready if id(m) not in cancelled]

    def find_simultaneous(self, ready: list[PendingMove]) -> set[Position]:
        """Return targets where multiple pieces arrive at the same time — O(M)."""
        groups = _group_by_target(ready)
        return {target for (_, target), moves in groups.items() if len(moves) > 1}

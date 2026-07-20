import json
from core.model.board import Board
from core.model.game_state import GameState
from core.events.event_bus import EventBus, MoveApplied, Capture, KingCaptured, Collision, PawnPromoted


def _piece_str(piece) -> str | None:
    if piece is None:
        return None
    return piece.color.value[0].upper() + piece.type.value.upper()


def _serialize_events(events: list) -> list:
    result = []
    for e in events:
        if isinstance(e, MoveApplied):
            result.append({"type": "move_applied",
                           "source": [e.source.row, e.source.col],
                           "target": [e.target.row, e.target.col]})
        elif isinstance(e, Capture):
            result.append({"type": "capture",
                           "capturing_color": e.capturing_color.value,
                           "captured_piece": e.captured_piece.to_str()})
        elif isinstance(e, KingCaptured):
            result.append({"type": "king_captured",
                           "pos": [e.pos.row, e.pos.col]})
        elif isinstance(e, Collision):
            result.append({"type": "collision",
                           "pos": [e.pos.row, e.pos.col]})
        elif isinstance(e, PawnPromoted):
            result.append({"type": "pawn_promoted",
                           "pos": [e.pos.row, e.pos.col]})
    return result


def make_event_collector(bus: EventBus) -> list:
    """Subscribe to all events and collect them into a list."""
    collected = []
    for event_type in (MoveApplied, Capture, KingCaptured, Collision, PawnPromoted):
        bus.subscribe(event_type, collected.append)
    return collected


def serialize(board: Board, state: GameState, events: list = None, white_name: str = "White", black_name: str = "Black") -> str:
    return json.dumps({
        "board": [
            [_piece_str(board.matrix[r][c]) for c in range(len(board.matrix[r]))]
            for r in range(len(board.matrix))
        ],
        "time":      state.current_time,
        "game_over": state.game_over,
        "pending_moves": [
            {"source": [m.source.row, m.source.col],
             "target": [m.target.row, m.target.col],
             "arrival": m.arrival}
            for m in state.pending_moves
        ],
        "cooldowns": {
            f"{pos.row},{pos.col}": t for pos, t in state.cooldowns.items()
        },
        "airborne": [
            {"cell": [a.cell.row, a.cell.col], "landing_time": a.landing_time}
            for a in state.airborne
        ],
        "events": _serialize_events(events or []),
        "white_name": white_name,
        "black_name": black_name,
    })

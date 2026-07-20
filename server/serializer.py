import json
from core.model.board import Board
from core.model.game_state import GameState


def _piece_str(piece) -> str | None:
    if piece is None:
        return None
    return piece.color.value[0].upper() + piece.type.value.upper()


def serialize(board: Board, state: GameState) -> str:
    return json.dumps({
        "board": [
            [_piece_str(board.matrix[r][c]) for c in range(len(board.matrix[r]))]
            for r in range(len(board.matrix))
        ],
        "time":     state.current_time,
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
    })

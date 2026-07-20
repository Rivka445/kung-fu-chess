import json
import asyncio
import threading
import websockets.sync.client as ws_sync
from core.model.position import Position, to_chess_notation, from_chess_notation
from core.model.board import Board
from core.model.game_state import GameState, PendingMove
from core.model.piece import Piece, PieceType, Color
from ui.server_bridge.base import ServerBridge

HOST = "localhost"
PORT = 8765
ROWS = 8

_PIECE_MAP = {
    "WP": (Color.WHITE, PieceType.PAWN),   "BP": (Color.BLACK, PieceType.PAWN),
    "WR": (Color.WHITE, PieceType.ROOK),   "BR": (Color.BLACK, PieceType.ROOK),
    "WN": (Color.WHITE, PieceType.KNIGHT), "BN": (Color.BLACK, PieceType.KNIGHT),
    "WB": (Color.WHITE, PieceType.BISHOP), "BB": (Color.BLACK, PieceType.BISHOP),
    "WQ": (Color.WHITE, PieceType.QUEEN),  "BQ": (Color.BLACK, PieceType.QUEEN),
    "WK": (Color.WHITE, PieceType.KING),   "BK": (Color.BLACK, PieceType.KING),
}


def _parse_state(data: dict, board: Board, state: GameState):
    """Update board and state in-place from server JSON."""
    rows = data["board"]
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell is None:
                board.matrix[r][c] = None
            else:
                color, ptype = _PIECE_MAP[cell]
                board.matrix[r][c] = Piece(color, ptype)

    state.current_time = data["time"]
    state.game_over    = data["game_over"]
    state.pending_moves = [
        PendingMove(
            Position(*m["source"]),
            Position(*m["target"]),
            m["arrival"]
        )
        for m in data["pending_moves"]
    ]
    state.cooldowns = {
        Position(int(k.split(",")[0]), int(k.split(",")[1])): v
        for k, v in data["cooldowns"].items()
    }


class WebSocketBridge(ServerBridge):
    def __init__(self):
        self._conn   = None
        self._board  = Board()
        self._state  = GameState()
        self._lock   = threading.Lock()

    def connect(self) -> None:
        self._conn = ws_sync.connect(f"ws://{HOST}:{PORT}")
        raw = self._conn.recv()
        with self._lock:
            _parse_state(json.loads(raw), self._board, self._state)

    def _send(self, cmd: str):
        if self._conn is None:
            return
        self._conn.send(cmd)
        raw = self._conn.recv()
        with self._lock:
            _parse_state(json.loads(raw), self._board, self._state)

    def send_move(self, source: Position, target: Position) -> None:
        self._send(f"M {to_chess_notation(source, ROWS)} {to_chess_notation(target, ROWS)}")

    def send_jump(self, pos: Position) -> None:
        self._send(f"J {to_chess_notation(pos, ROWS)}")

    def get_board(self) -> Board:
        with self._lock:
            return self._board

    def get_state(self) -> GameState:
        with self._lock:
            return self._state

    def advance_time(self, ms: int) -> None:
        self._send(f"T {ms}")

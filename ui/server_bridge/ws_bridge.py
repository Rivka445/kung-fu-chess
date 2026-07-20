import json
import threading
import websockets.sync.client as ws_sync
from core.model.position import Position, to_chess_notation, from_chess_notation
from core.model.board import Board
from core.model.game_state import GameState, PendingMove, AirbornePiece
from core.model.piece import Piece, PieceType, Color
from core.events.event_bus import EventBus, MoveApplied, Capture, KingCaptured, Collision, PawnPromoted
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
    rows = data["board"]
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell is None:
                board.matrix[r][c] = None
            else:
                color, ptype = _PIECE_MAP[cell]
                board.matrix[r][c] = Piece(color, ptype)

    state.current_time  = data["time"]
    state.game_over     = data["game_over"]
    state.pending_moves = [
        PendingMove(Position(*m["source"]), Position(*m["target"]), m["arrival"])
        for m in data["pending_moves"]
    ]
    state.cooldowns = {
        Position(int(k.split(",")[0]), int(k.split(",")[1])): v
        for k, v in data["cooldowns"].items()
    }
    state.airborne = [
        AirbornePiece(Position(*a["cell"]), a["landing_time"])
        for a in data["airborne"]
    ]


def _publish_events(data: dict, bus: EventBus):
    for e in data.get("events", []):
        t = e["type"]
        if t == "move_applied":
            bus.publish(MoveApplied(Position(*e["source"]), Position(*e["target"])))
        elif t == "capture":
            bus.publish(Capture(None, Color(e["capturing_color"])))
        elif t == "king_captured":
            bus.publish(KingCaptured(Position(*e["pos"])))
        elif t == "collision":
            bus.publish(Collision(Position(*e["pos"])))
        elif t == "pawn_promoted":
            bus.publish(PawnPromoted(Position(*e["pos"])))


class WebSocketBridge(ServerBridge):
    def __init__(self, bus: EventBus, username: str = "Player"):
        self._conn     = None
        self._board    = Board()
        self._state    = GameState()
        self._lock     = threading.Lock()
        self._bus      = bus
        self._username = username

    def _send(self, cmd: str):
        """Send a command to the server and update local state from response."""
        if self._conn is None:
            return
        self._conn.send(cmd)
        data = json.loads(self._conn.recv())
        with self._lock:
            _parse_state(data, self._board, self._state)
        _publish_events(data, self._bus)

    def connect(self) -> None:
        self._conn = ws_sync.connect(f"ws://{HOST}:{PORT}")
        self._conn.send(f"LOGIN {self._username}")
        raw = self._conn.recv()
        if raw == "WAITING":
            print(f"[{self._username}] Waiting for second player...")
            raw = self._conn.recv()
        data = json.loads(raw)
        with self._lock:
            _parse_state(data, self._board, self._state)

    def send_move(self, source: Position, target: Position) -> None:
        t = self._state.current_time
        self._send(f"M {to_chess_notation(source, ROWS)} {to_chess_notation(target, ROWS)} {t}")

    def send_jump(self, pos: Position) -> None:
        t = self._state.current_time
        self._send(f"J {to_chess_notation(pos, ROWS)} {t}")

    def get_board(self) -> Board:
        with self._lock:
            return self._board

    def get_state(self) -> GameState:
        with self._lock:
            return self._state

    def advance_time(self, ms: int) -> None:
        """Advance time locally — no server round-trip every frame."""
        with self._lock:
            self._state.current_time += ms

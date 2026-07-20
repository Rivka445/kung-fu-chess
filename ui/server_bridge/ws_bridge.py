import json
import threading
import websockets.sync.client as ws_sync
from core.model.position import Position, to_chess_notation, from_chess_notation
from core.model.board import Board
from core.model.game_state import GameState, PendingMove, AirbornePiece
from core.model.piece import Piece, PieceType, Color
from core.events.event_bus import EventBus, MoveApplied, Capture, KingCaptured, Collision, PawnPromoted
from ui.server_bridge.base import ServerBridge
from logger import logger

HOST = "localhost"
PORT = 8765
ROWS = 8
TICK_MS = 50  # minimum real time between server sync ticks

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
    board.matrix = [
        [None if cell is None else Piece(*_PIECE_MAP[cell]) for cell in row]
        for row in rows
    ]
    board.expected_cols = len(rows[0]) if rows else None

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
    return data.get("white_name", "White"), data.get("black_name", "Black")


def _publish_events(data: dict, bus: EventBus):
    for e in data.get("events", []):
        t = e["type"]
        if t == "move_applied":
            bus.publish(MoveApplied(Position(*e["source"]), Position(*e["target"])))
        elif t == "capture":
            bus.publish(Capture(Piece.from_str(e["captured_piece"]), Color(e["capturing_color"])))
        elif t == "king_captured":
            bus.publish(KingCaptured(Position(*e["pos"])))
        elif t == "collision":
            bus.publish(Collision(Position(*e["pos"])))
        elif t == "pawn_promoted":
            bus.publish(PawnPromoted(Position(*e["pos"])))


class WebSocketBridge(ServerBridge):
    """
    The server pushes a fresh state to BOTH players after any single player's
    command (so opponent moves show up too) — it is not a strict 1-reply-per-
    request protocol. A dedicated background thread drains every incoming
    message as it arrives and applies it to local state; sending never blocks
    waiting for "its own" reply. Pairing one send with one blocking recv() (the
    earlier approach) caused clients to occasionally consume a message meant
    for a different purpose, leaving a growing backlog that made the game
    appear to freeze or apply moves after a long delay.
    """

    def __init__(self, bus: EventBus, username: str = "Player"):
        self._conn       = None
        self._board      = Board()
        self._state      = GameState()
        self._lock       = threading.Lock()
        self._bus        = bus
        self._username   = username
        self.player_names = {Color.WHITE: "White", Color.BLACK: "Black"}
        self._tick_accum = 0

    def _apply(self, raw: str):
        data = json.loads(raw)
        with self._lock:
            wn, bn = _parse_state(data, self._board, self._state)
            self.player_names[Color.WHITE] = wn
            self.player_names[Color.BLACK] = bn
        _publish_events(data, self._bus)

    def _recv_loop(self):
        while True:
            try:
                raw = self._conn.recv()
            except Exception:
                return
            try:
                self._apply(raw)
            except Exception:
                logger.exception("failed to apply server state — skipping this message")

    def connect(self) -> None:
        self._conn = ws_sync.connect(f"ws://{HOST}:{PORT}")
        self._conn.send(f"LOGIN {self._username}")
        raw = self._conn.recv()
        if raw == "WAITING":
            print(f"[{self._username}] Waiting for second player...")
            raw = self._conn.recv()
        self._apply(raw)
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def send_move(self, source: Position, target: Position) -> None:
        with self._lock:
            t = self._state.current_time
        self._conn.send(f"M {to_chess_notation(source, ROWS)} {to_chess_notation(target, ROWS)} {t}")

    def send_jump(self, pos: Position) -> None:
        with self._lock:
            t = self._state.current_time
        self._conn.send(f"J {to_chess_notation(pos, ROWS)} {t}")

    def get_board(self) -> Board:
        with self._lock:
            return self._board

    def get_state(self) -> GameState:
        with self._lock:
            return self._state

    def advance_time(self, ms: int) -> None:
        """
        Advance time locally for smooth animation, and periodically ping the
        server (every TICK_MS) so pending moves actually resolve server-side —
        otherwise a move stays queued forever unless another command happens
        to push the server's clock past its arrival time. The reply (like any
        other incoming message) is picked up by the background reader thread.
        """
        with self._lock:
            self._state.current_time += ms
        self._tick_accum += ms
        if self._tick_accum >= TICK_MS:
            elapsed, self._tick_accum = self._tick_accum, 0
            self._conn.send(f"T {elapsed}")

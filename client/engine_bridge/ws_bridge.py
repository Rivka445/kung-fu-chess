import getpass
import json
import threading
import websockets.sync.client as ws_sync
from core.model.position import Position, to_chess_notation, from_chess_notation
from core.model.board import Board
from core.model.game_state import GameState, PendingMove, AirbornePiece
from core.model.piece import Piece, PieceType, Color
from core.events.event_bus import (EventBus, MoveApplied, Capture, KingCaptured, Collision,
                                    PawnPromoted, GameStarted, GameOver)
from client.engine_bridge.base import EngineBridge
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
    state.disconnect_seconds_left = data.get("disconnect_seconds_left")
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
    return (data.get("white_name", "White"), data.get("black_name", "Black"),
            data.get("white_rating", 1200), data.get("black_rating", 1200))


# wire type name -> event builder
_EVENT_BUILDERS = {
    "move_applied":  lambda e: MoveApplied(Position(*e["source"]), Position(*e["target"])),
    "capture":       lambda e: Capture(Piece.from_str(e["captured_piece"]), Color(e["capturing_color"])),
    "king_captured": lambda e: KingCaptured(Position(*e["pos"])),
    "collision":     lambda e: Collision(Position(*e["pos"])),
    "pawn_promoted": lambda e: PawnPromoted(Position(*e["pos"])),
    "game_started":  lambda e: GameStarted(),
    "game_ended":    lambda e: GameOver(),
}


def _publish_events(data: dict, bus: EventBus):
    for e in data.get("events", []):
        builder = _EVENT_BUILDERS.get(e["type"])
        if builder:
            bus.publish(builder(e))


class WebSocketBridge(EngineBridge):
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
        self.ratings      = {Color.WHITE: 1200, Color.BLACK: 1200}
        self._tick_accum = 0
        # None -> "searching" (Play clicked) -> "matched" or "timed_out" (NO_MATCH)
        self.search_status = None
        self._bus.subscribe(GameOver, self._on_game_over)

    def _apply(self, raw: str):
        data = json.loads(raw)
        with self._lock:
            wn, bn, wr, br = _parse_state(data, self._board, self._state)
            self.player_names[Color.WHITE] = wn
            self.player_names[Color.BLACK] = bn
            self.ratings[Color.WHITE] = wr
            self.ratings[Color.BLACK] = br
        _publish_events(data, self._bus)

    def _on_game_over(self, _event):
        with self._lock:
            my_color = Color.WHITE if self.player_names[Color.WHITE] == self._username else Color.BLACK
            my_rating = self.ratings[my_color]
        print(f"\nGame over — your new rating: {my_rating}")

    def _recv_loop(self):
        while True:
            try:
                raw = self._conn.recv()
            except Exception:
                return
            if raw == "WAITING":
                continue
            if raw == "NO_MATCH":
                self.search_status = "timed_out"
                continue
            try:
                self._apply(raw)
                self.search_status = "matched"
            except Exception:
                logger.exception("failed to apply server state — skipping this message")

    def login(self) -> None:
        """
        Prompt for a password in the shell and log in. LOGIN <username> <password>
        is verified server-side against SQLite (auto-registers unknown usernames).
        The server closes the connection on rejection, so a retry opens a fresh one.
        Starts the background receive thread right after login — matchmaking now
        happens later (start_search), so WAITING/NO_MATCH/state messages can arrive
        at any point after this and must already be handled.
        """
        while True:
            self._conn = ws_sync.connect(f"ws://{HOST}:{PORT}")
            password = getpass.getpass(f"Password for {self._username}: ")
            self._conn.send(f"LOGIN {self._username} {password}")
            reply = self._conn.recv()
            if reply.startswith("ERR"):
                print(f"Login failed: {reply[4:]}")
                self._conn.close()
                continue
            rating = int(reply.split()[1])
            print(f"Logged in as {self._username} (rating: {rating})")
            break
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def start_search(self) -> None:
        """Ask the server to start matchmaking (Play button)."""
        self.search_status = "searching"
        self._conn.send("PLAY")

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

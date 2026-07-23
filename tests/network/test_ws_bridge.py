import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.model.board import Board
from shared.model.position import Position
from shared.model.piece import Piece, Color
from shared.model.game_state import GameState, PendingMove, AirbornePiece
from shared.events.event_bus import EventBus, MoveApplied, GameOver
from shared.protocol.serializer import serialize
from server.utils.board_parser import parse_row
from client.engine_bridge import ws_bridge
from client.engine_bridge.ws_bridge import WebSocketBridge


class FakeConn:
    """Stand-in for a websockets.sync.client connection."""

    def __init__(self, replies=None):
        self._replies = list(replies or [])
        self.sent = []
        self.closed = False

    def send(self, msg):
        self.sent.append(msg)

    def recv(self):
        if not self._replies:
            raise ConnectionError("closed")
        return self._replies.pop(0)

    def close(self):
        self.closed = True


def _bridge_with_conn(conn, username="Player"):
    bridge = WebSocketBridge(EventBus(), username=username)
    bridge._conn = conn
    return bridge


# ---- send_move / send_jump ----

def test_send_move_formats_wire_message():
    conn = FakeConn()
    bridge = _bridge_with_conn(conn)
    bridge._state.current_time = 500
    bridge.send_move(Position(6, 0), Position(4, 0))
    assert conn.sent == ["M a2 a4 500"]


def test_send_jump_formats_wire_message():
    conn = FakeConn()
    bridge = _bridge_with_conn(conn)
    bridge._state.current_time = 250
    bridge.send_jump(Position(1, 1))
    assert conn.sent == ["J b7 250"]


# ---- advance_time tick throttling ----

def test_advance_time_only_pings_server_once_tick_threshold_reached():
    conn = FakeConn()
    bridge = _bridge_with_conn(conn)

    bridge.advance_time(30)
    assert conn.sent == []
    assert bridge.get_state().current_time == 30

    bridge.advance_time(30)
    assert conn.sent == ["T 60"]
    assert bridge.get_state().current_time == 60
    assert bridge._tick_accum == 0


# ---- _apply: board/state reconstruction + event forwarding ----

def _build_source_state():
    board = Board()
    board.add_parsed_row(parse_row("wK . bR", 3))
    board.add_parsed_row(parse_row(". . .", 3))
    state = GameState(current_time=1234, disconnect_seconds_left=5)
    state.pending_moves.append(PendingMove(Position(0, 2), Position(0, 0), arrival=3000))
    state.cooldowns[Position(1, 1)] = 2000
    state.airborne.append(AirbornePiece(Position(0, 0), landing_time=1500))
    return board, state


def test_apply_reconstructs_board_and_state_from_wire_format():
    board, state = _build_source_state()
    raw = serialize(board, state, events=[], white_name="Ann", black_name="Ben",
                     white_rating=1300, black_rating=1100, disconnect_seconds_left=5)

    bridge = _bridge_with_conn(FakeConn(), username="Ann")
    bridge._apply(raw)

    got_board = bridge.get_board()
    assert got_board.get_piece(Position(0, 0)) == Piece.from_str("wK")
    assert got_board.get_piece(Position(0, 2)) == Piece.from_str("bR")

    got_state = bridge.get_state()
    assert got_state.current_time == 1234
    assert got_state.disconnect_seconds_left == 5
    assert got_state.pending_moves == [PendingMove(Position(0, 2), Position(0, 0), 3000)]
    assert got_state.cooldowns == {Position(1, 1): 2000}
    assert got_state.airborne == [AirbornePiece(Position(0, 0), landing_time=1500)]

    assert bridge.player_names[Color.WHITE] == "Ann"
    assert bridge.player_names[Color.BLACK] == "Ben"
    assert bridge.ratings[Color.WHITE] == 1300
    assert bridge.ratings[Color.BLACK] == 1100


def test_apply_forwards_events_onto_local_bus():
    board, state = _build_source_state()
    raw = serialize(board, state, events=[MoveApplied(Position(0, 0), Position(0, 1))])

    bus = EventBus()
    received = []
    bus.subscribe(MoveApplied, received.append)

    bridge = WebSocketBridge(bus, username="Ann")
    bridge._conn = FakeConn()
    bridge._apply(raw)

    assert received == [MoveApplied(Position(0, 0), Position(0, 1))]


def test_on_game_over_prints_this_players_new_rating(capsys):
    bus = EventBus()
    bridge = WebSocketBridge(bus, username="Ann")
    bridge._conn = FakeConn()
    bridge.player_names = {Color.WHITE: "Ann", Color.BLACK: "Ben"}
    bridge.ratings = {Color.WHITE: 1300, Color.BLACK: 1100}

    bus.publish(GameOver())

    out = capsys.readouterr().out
    assert "1300" in out


# ---- login ----

def test_login_success_sends_credentials_and_prints_rating(monkeypatch, capsys):
    conn = FakeConn(replies=["OK 1200"])
    monkeypatch.setattr(ws_bridge.ws_sync, "connect", lambda url: conn)
    monkeypatch.setattr(ws_bridge.getpass, "getpass", lambda prompt: "hunter2")

    bridge = WebSocketBridge(EventBus(), username="alice")
    bridge.login()

    assert conn.sent == ["LOGIN alice hunter2"]
    assert "Logged in as alice (rating: 1200)" in capsys.readouterr().out


def test_login_retries_after_rejection(monkeypatch, capsys):
    attempts = [FakeConn(replies=["ERR wrong_password"]), FakeConn(replies=["OK 1250"])]
    monkeypatch.setattr(ws_bridge.ws_sync, "connect", lambda url: attempts.pop(0))
    monkeypatch.setattr(ws_bridge.getpass, "getpass", lambda prompt: "hunter2")

    bridge = WebSocketBridge(EventBus(), username="alice")
    bridge.login()

    out = capsys.readouterr().out
    assert "Login failed: wrong_password" in out
    assert "Logged in as alice (rating: 1250)" in out

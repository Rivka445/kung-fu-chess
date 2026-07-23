import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import contextlib
import pytest
from shared.model.piece import Color
from server.db.db import AuthError
from server.services.matchmaker import Matchmaker
from server.game.session import GameSession
from server.network import game_server


pytestmark = pytest.mark.asyncio


class FakeWS:
    """
    Minimal stand-in for a server-side websockets connection. Supports both
    `await ws.recv()` and `async for message in ws` against the same queue —
    real websocket connections allow both against one shared incoming buffer,
    and game_server.py's handle()/_play()/_find_match() mix both styles
    across a single connection's lifetime.
    """

    def __init__(self, incoming=None):
        self._incoming = list(incoming or [])
        self.sent = []
        self.closed = False

    async def recv(self):
        if not self._incoming:
            raise RuntimeError("no more scripted messages")
        return self._incoming.pop(0)

    async def send(self, msg):
        self.sent.append(msg)

    async def close(self):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)


async def _cancel(task):
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


# ---- _login ----

async def test_login_rejects_malformed_first_message():
    ws = FakeWS(["hello"])
    result = await game_server._login(ws)
    assert result is None
    assert ws.closed


async def test_login_rejects_wrong_password(monkeypatch):
    monkeypatch.setattr(game_server, "authenticate_or_register",
                         lambda u, p: (_ for _ in ()).throw(AuthError("wrong password")))

    ws = FakeWS(["LOGIN alice badpw"])
    result = await game_server._login(ws)

    assert result is None
    assert ws.closed
    assert ws.sent == ["ERR wrong password"]


async def test_login_success_returns_username_and_rating(monkeypatch):
    monkeypatch.setattr(game_server, "authenticate_or_register", lambda u, p: 1234)

    ws = FakeWS(["LOGIN alice pw"])
    result = await game_server._login(ws)

    assert result == ("alice", 1234)
    assert ws.sent == ["OK 1234"]
    assert not ws.closed


# ---- _find_match ----

async def test_find_match_ignores_chatter_until_play(monkeypatch):
    monkeypatch.setattr(game_server, "matchmaker", Matchmaker())

    ws_a = FakeWS(["PLAY"])
    ws_b = FakeWS(["not play yet", "PLAY"])

    task_a = asyncio.create_task(game_server._find_match(ws_a, "alice", 1200))
    await asyncio.sleep(0)
    result_b = await game_server._find_match(ws_b, "bob", 1250)
    result_a = await task_a

    color_a, session_a = result_a
    color_b, session_b = result_b
    assert session_a is session_b
    assert {color_a, color_b} == {Color.WHITE, Color.BLACK}


async def test_find_match_sends_no_match_on_search_timeout(monkeypatch):
    monkeypatch.setattr(game_server, "matchmaker", Matchmaker())
    monkeypatch.setattr(game_server, "SEARCH_TIMEOUT_S", 0.05)

    ws = FakeWS(["PLAY"])
    result = await game_server._find_match(ws, "alice", 1200)

    assert result is None
    assert ws.sent == ["NO_MATCH"]


# ---- _play ----

async def test_play_dispatches_move_and_broadcasts_to_both_sockets():
    session = GameSession()
    ws_white = FakeWS(["M e2 e4 0"])
    ws_black = FakeWS()
    session.sockets[Color.WHITE] = ws_white
    session.sockets[Color.BLACK] = ws_black
    session.names[Color.WHITE] = "alice"
    session.names[Color.BLACK] = "bob"

    await game_server._play(ws_white, session, Color.WHITE)

    # 1 initial broadcast + 1 after the move command = 2 messages each side.
    assert len(ws_white.sent) == 2
    assert len(ws_black.sent) == 2
    assert len(session.engine.state.pending_moves) == 1

    await _cancel(session._disconnect_task)


async def test_play_ignores_unknown_command_without_extra_broadcast():
    session = GameSession()
    ws_white = FakeWS(["GARBAGE"])
    ws_black = FakeWS()
    session.sockets[Color.WHITE] = ws_white
    session.sockets[Color.BLACK] = ws_black

    await game_server._play(ws_white, session, Color.WHITE)

    assert len(ws_white.sent) == 1  # only the initial broadcast
    assert len(ws_black.sent) == 1

    await _cancel(session._disconnect_task)


async def test_play_starts_disconnect_countdown_when_client_stops_sending():
    session = GameSession()
    ws_white = FakeWS([])
    session.sockets[Color.WHITE] = ws_white
    session.sockets[Color.BLACK] = FakeWS()

    await game_server._play(ws_white, session, Color.WHITE)

    assert session._disconnect_task is not None
    await _cancel(session._disconnect_task)


# ---- handle(): full login -> match -> play flow with two simulated clients ----

async def test_handle_runs_full_two_player_flow(monkeypatch):
    monkeypatch.setattr(game_server, "matchmaker", Matchmaker())
    monkeypatch.setattr(game_server, "authenticate_or_register", lambda u, p: 1200)
    monkeypatch.setattr("server.game.session.DISCONNECT_TIMEOUT_S", 0.01)

    ws_white = FakeWS(["LOGIN alice pw", "PLAY", "M e2 e4 0"])
    ws_black = FakeWS(["LOGIN bob pw", "PLAY"])

    await asyncio.gather(game_server.handle(ws_white), game_server.handle(ws_black))

    assert ws_white.sent[0] == "OK 1200"
    assert ws_black.sent[0] == "OK 1200"
    # Both sides received at least the post-match game state beyond the login reply.
    assert len(ws_white.sent) >= 2
    assert len(ws_black.sent) >= 2

    await asyncio.sleep(0.05)  # let the short-lived disconnect-countdown tasks finish

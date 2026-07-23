import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import json
import pytest
import websockets
from server.network import game_server
from server.services.matchmaker import Matchmaker


pytestmark = pytest.mark.asyncio


async def _run_scenario():
    async with websockets.connect(_run_scenario.url) as client_a, \
               websockets.connect(_run_scenario.url) as client_b:

        await client_a.send("LOGIN alice pw")
        await client_b.send("LOGIN bob pw")
        assert await client_a.recv() == "OK 1200"
        assert await client_b.recv() == "OK 1200"

        await client_a.send("PLAY")
        await client_b.send("PLAY")

        state_a = json.loads(await client_a.recv())
        state_b = json.loads(await client_b.recv())

        # Both clients were pushed the identical post-match board/state.
        assert state_a["board"] == state_b["board"]
        assert {state_a["white_name"], state_a["black_name"]} == {"alice", "bob"}

        white_client = client_a if state_a["white_name"] == "alice" else client_b
        await white_client.send("M e2 e4 0")

        update_a = json.loads(await client_a.recv())
        update_b = json.loads(await client_b.recv())
        assert update_a == update_b
        assert len(update_a["pending_moves"]) == 1


async def test_two_real_websocket_clients_login_match_and_move(monkeypatch):
    """
    End-to-end check over a real localhost TCP socket (not a fake/mocked
    connection): starts the actual game_server.handle() behind a real
    websockets.serve(), connects two real websocket clients, and drives them
    through LOGIN -> PLAY -> matched -> a queued move, exactly like the real
    two-player demo described in the run instructions.
    """
    monkeypatch.setattr(game_server, "matchmaker", Matchmaker())
    monkeypatch.setattr(game_server, "authenticate_or_register", lambda u, p: 1200)
    monkeypatch.setattr("server.game.session.DISCONNECT_TIMEOUT_S", 0.2)

    server = await websockets.serve(game_server.handle, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    _run_scenario.url = f"ws://localhost:{port}"
    try:
        await asyncio.wait_for(_run_scenario(), timeout=10)
    finally:
        server.close()
        await server.wait_closed()
        # Let the disconnect-countdown tasks started when the client sockets
        # closed run to completion instead of being destroyed mid-flight.
        await asyncio.sleep(0.3)

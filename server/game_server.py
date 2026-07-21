import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
from core.model.piece import Color
from server.game_session import dispatch
from server.matchmaker import Matchmaker, SEARCH_TIMEOUT_S
from server.db import authenticate_or_register, AuthError
from logger import logger

HOST = "localhost"
PORT = 8765

matchmaker = Matchmaker()


async def handle(ws):
    # ── LOGIN ──────────────────────────────────────────────────────────────
    first = (await ws.recv()).strip().split()
    if len(first) < 3 or first[0].upper() != "LOGIN":
        await ws.close()
        return
    username, password = first[1], first[2]

    try:
        rating = authenticate_or_register(username, password)
    except AuthError as e:
        logger.info("[server] login rejected for %s: %s", username, e)
        await ws.send(f"ERR {e}")
        await ws.close()
        return

    await ws.send(f"OK {rating}")

    # ── LOBBY ──────────────────────────────────────────────────────────────
    # Wait for the client to explicitly ask to search ("PLAY" = clicking the
    # Play button). A search that times out sends NO_MATCH and lets the
    # client retry with another PLAY on this same, already-authenticated
    # connection instead of logging in again.
    color = session = None
    async for message in ws:
        if message.strip().upper() != "PLAY":
            continue
        try:
            color, session = await asyncio.wait_for(
                matchmaker.join(ws, username, rating), timeout=SEARCH_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.info("[server] %s found no match within %ss", username, SEARCH_TIMEOUT_S)
            await ws.send("NO_MATCH")
            continue
        break

    if session is None:
        return  # socket closed while still in the lobby

    logger.info("[server] %s (%s) ready", username, "White" if color == Color.WHITE else "Black")

    # Send initial state
    await session.send_state(ws)
    session.events.clear()

    # ── GAME LOOP ──────────────────────────────────────────────────────────
    try:
        async for message in ws:
            parts = message.strip().split()
            if not parts:
                continue

            cmd = parts[0].upper()

            result = dispatch(session, cmd, parts, color)
            if result is None:
                logger.debug("[server] unknown command: %r", message)
                continue
            if not result:
                continue

            await session.broadcast()
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if not session.engine.state.game_over:
            session.handle_disconnect(color)


async def main():
    logger.info("[server] listening on ws://%s:%s", HOST, PORT)
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
from core.model.piece import Color
from server.game_session import dispatch
from server.matchmaker import Matchmaker
from logger import logger

HOST = "localhost"
PORT = 8765

matchmaker = Matchmaker()


async def handle(ws):
    # ── LOGIN ──────────────────────────────────────────────────────────────
    first = (await ws.recv()).strip().split()
    if len(first) < 2 or first[0].upper() != "LOGIN":
        await ws.close()
        return
    username = first[1]

    # ── LOBBY ──────────────────────────────────────────────────────────────
    color, session = await matchmaker.join(ws, username)

    logger.info("[server] %s (%s) ready", username, "White" if color == Color.WHITE else "Black")

    # Send initial state
    await session.send_state(ws)
    session.events.clear()

    # ── GAME LOOP ──────────────────────────────────────────────────────────
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


async def main():
    logger.info("[server] listening on ws://%s:%s", HOST, PORT)
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

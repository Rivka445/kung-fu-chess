import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
from core.model.piece import Color
from server.game_session import dispatch, GameSession
from server.matchmaker import Matchmaker, SEARCH_TIMEOUT_S
from server.db import authenticate_or_register, AuthError
from logger import logger

HOST = "localhost"
PORT = 8765

matchmaker = Matchmaker()


async def _login(ws) -> tuple[str, int] | None:
    """Authenticate the socket. Returns (username, rating), or None if rejected/closed."""
    first = (await ws.recv()).strip().split()
    if len(first) < 3 or first[0].upper() != "LOGIN":
        await ws.close()
        return None
    username, password = first[1], first[2]

    try:
        rating = authenticate_or_register(username, password)
    except AuthError as e:
        logger.info("[server] login rejected for %s: %s", username, e)
        await ws.send(f"ERR {e}")
        await ws.close()
        return None

    await ws.send(f"OK {rating}")
    return username, rating


async def _find_match(ws, username: str, rating: int) -> tuple[Color, GameSession] | None:
    """
    Waits for a "PLAY" message before searching — matchmaking doesn't start
    right after login. A timed-out search sends NO_MATCH and lets the client
    retry with PLAY again on the same connection, without logging in again.
    """
    async for message in ws:
        if message.strip().upper() != "PLAY":
            continue
        try:
            return await asyncio.wait_for(
                matchmaker.join(ws, username, rating), timeout=SEARCH_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.info("[server] %s found no match within %ss", username, SEARCH_TIMEOUT_S)
            await ws.send("NO_MATCH")
    return None


async def _play(ws, session: GameSession, color: Color) -> None:
    # Send the initial post-match state to both players exactly once — see
    # send_initial_broadcast's docstring for why a plain per-connection
    # send_state+clear here would race and could drop GameStarted for
    # whichever side's coroutine resumes second.
    await session.send_initial_broadcast()

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


async def handle(ws):
    login_result = await _login(ws)
    if login_result is None:
        return
    username, rating = login_result

    match_result = await _find_match(ws, username, rating)
    if match_result is None:
        return
    color, session = match_result

    logger.info("[server] %s (%s) ready", username, "White" if color == Color.WHITE else "Black")

    await _play(ws, session, color)


async def main():
    logger.info("[server] listening on ws://%s:%s", HOST, PORT)
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

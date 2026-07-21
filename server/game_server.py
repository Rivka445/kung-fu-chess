import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
from core.engine.game_builder import GameBuilder
from core.model.position import from_chess_notation
from core.model.piece import Color
from server.serializer import serialize, make_event_collector
from constants import DEFAULT_BOARD
from logger import logger

HOST = "localhost"
PORT = 8765
ROWS = 8

_engine  = None
_events  = None
_waiting = None   # (ws, username, asyncio.Event)
_session = None   # (ws_white, ws_black)
_names   = {}     # {Color.WHITE: name, Color.BLACK: name}


def _build_engine():
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    return builder.build().engine


async def _send_state(ws):
    await ws.send(serialize(_engine.board, _engine.state, _events,
                            white_name=_names.get(Color.WHITE, "White"),
                            black_name=_names.get(Color.BLACK, "Black")))


def _cmd_move(parts, color):
    if len(parts) < 3:
        return None
    src = from_chess_notation(parts[1], ROWS)
    tgt = from_chess_notation(parts[2], ROWS)
    if len(parts) >= 4:
        _engine.advance_time(int(parts[3]) - _engine.state.current_time)
    piece = _engine.board.get_piece(src)
    if piece is None or piece.color != color:
        return False
    _engine.request_move(src, tgt)
    return True


def _cmd_jump(parts, color):
    if len(parts) < 2:
        return None
    pos = from_chess_notation(parts[1], ROWS)
    if len(parts) >= 3:
        _engine.advance_time(int(parts[2]) - _engine.state.current_time)
    piece = _engine.board.get_piece(pos)
    if piece is None or piece.color != color:
        return False
    _engine.request_jump(pos)
    return True


def _cmd_time(parts, color):
    if len(parts) != 2:
        return None
    _engine.advance_time(int(parts[1]))
    return True


# cmd -> handler(parts, color) -> True (broadcast) / False (silent skip) / None (unknown/malformed)
COMMANDS = {"M": _cmd_move, "J": _cmd_jump, "T": _cmd_time}


async def handle(ws):
    global _engine, _events, _waiting, _session, _names

    # ── LOGIN ──────────────────────────────────────────────────────────────
    first = (await ws.recv()).strip().split()
    if len(first) < 2 or first[0].upper() != "LOGIN":
        await ws.close()
        return
    username = first[1]

    # ── LOBBY ──────────────────────────────────────────────────────────────
    if _waiting is None:
        # First player — build engine, wait for second
        _engine  = _build_engine()
        _events  = make_event_collector(_engine.bus)
        _names   = {}
        ready    = asyncio.Event()
        _waiting = (ws, username, ready)
        color    = Color.WHITE
        _names[Color.WHITE] = username
        logger.info("[lobby] %s joined as White — waiting for Black...", username)
        await ws.send("WAITING")
        await ready.wait()
        ws_white, ws_black = _session
    else:
        # Second player — release the first and start
        ws1, name1, ready = _waiting
        _waiting  = None
        color     = Color.BLACK
        _names[Color.BLACK] = username
        ws_white, ws_black = ws1, ws
        _session  = (ws_white, ws_black)
        logger.info("[lobby] %s joined as Black — starting game!", username)
        ready.set()

    logger.info("[server] %s (%s) ready", username, "White" if color == Color.WHITE else "Black")

    # Send initial state
    await _send_state(ws)
    _events.clear()

    ws_other = ws_black if color == Color.WHITE else ws_white

    # ── GAME LOOP ──────────────────────────────────────────────────────────
    async for message in ws:
        parts = message.strip().split()
        if not parts:
            continue

        cmd = parts[0].upper()

        handler = COMMANDS.get(cmd)
        result = handler(parts, color) if handler else None
        if result is None:
            logger.debug("[server] unknown command: %r", message)
            continue
        if not result:
            continue

        await _send_state(ws)
        try:
            await _send_state(ws_other)
        except Exception:
            pass
        _events.clear()


async def main():
    logger.info("[server] listening on ws://%s:%s", HOST, PORT)
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

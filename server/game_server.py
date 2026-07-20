import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
from core.engine.game_builder import GameBuilder
from core.model.position import from_chess_notation
from server.serializer import serialize, make_event_collector
from constants import DEFAULT_BOARD

HOST = "localhost"
PORT = 8765
ROWS = 8


def _build_engine():
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    return builder.build().engine


async def handle(ws):
    engine = _build_engine()
    events = make_event_collector(engine.bus)
    print(f"[server] client connected")

    async def send_state():
        await ws.send(serialize(engine.board, engine.state, events))
        events.clear()

    await send_state()

    async for message in ws:
        message = message.strip()
        parts   = message.split()

        if not parts:
            continue

        cmd = parts[0].upper()

        if cmd == "M" and len(parts) == 3:          # M e2 e4
            src = from_chess_notation(parts[1], ROWS)
            tgt = from_chess_notation(parts[2], ROWS)
            engine.request_move(src, tgt)

        elif cmd == "J" and len(parts) == 2:         # J e2
            pos = from_chess_notation(parts[1], ROWS)
            engine.request_jump(pos)

        elif cmd == "T" and len(parts) == 2:         # T 16
            engine.advance_time(int(parts[1]))

        else:
            print(f"[server] unknown command: {message!r}")
            continue

        await send_state()


async def main():
    print(f"[server] listening on ws://{HOST}:{PORT}")
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

from core.engine.game_builder import GameBuilder
from core.model.position import from_chess_notation
from core.model.piece import Color
from server.serializer import serialize, make_event_collector
from constants import DEFAULT_BOARD

ROWS = 8


def _build_engine():
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    return builder.build().engine


class GameSession:
    """One in-progress match: engine, collected events, player names and sockets."""

    def __init__(self):
        self.engine  = _build_engine()
        self.events  = make_event_collector(self.engine.bus)
        self.names   = {}   # {Color.WHITE: name, Color.BLACK: name}
        self.sockets = {}   # {Color.WHITE: ws, Color.BLACK: ws}

    async def send_state(self, ws):
        await ws.send(serialize(self.engine.board, self.engine.state, self.events,
                                white_name=self.names.get(Color.WHITE, "White"),
                                black_name=self.names.get(Color.BLACK, "Black")))

    async def broadcast(self):
        await self.send_state(self.sockets[Color.WHITE])
        try:
            await self.send_state(self.sockets[Color.BLACK])
        except Exception:
            pass
        self.events.clear()

    def _cmd_move(self, parts, color):
        if len(parts) < 3:
            return None
        src = from_chess_notation(parts[1], ROWS)
        tgt = from_chess_notation(parts[2], ROWS)
        if len(parts) >= 4:
            self.engine.advance_time(int(parts[3]) - self.engine.state.current_time)
        piece = self.engine.board.get_piece(src)
        if piece is None or piece.color != color:
            return False
        self.engine.request_move(src, tgt)
        return True

    def _cmd_jump(self, parts, color):
        if len(parts) < 2:
            return None
        pos = from_chess_notation(parts[1], ROWS)
        if len(parts) >= 3:
            self.engine.advance_time(int(parts[2]) - self.engine.state.current_time)
        piece = self.engine.board.get_piece(pos)
        if piece is None or piece.color != color:
            return False
        self.engine.request_jump(pos)
        return True

    def _cmd_time(self, parts, color):
        if len(parts) != 2:
            return None
        self.engine.advance_time(int(parts[1]))
        return True


# cmd -> handler(session, parts, color) -> True (broadcast) / False (silent skip) / None (unknown/malformed)
COMMANDS = {"M": GameSession._cmd_move, "J": GameSession._cmd_jump, "T": GameSession._cmd_time}


def dispatch(session: GameSession, cmd: str, parts: list, color: Color):
    handler = COMMANDS.get(cmd)
    return handler(session, parts, color) if handler else None

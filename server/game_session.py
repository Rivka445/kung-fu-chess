import asyncio
import time
from core.engine.game_builder import GameBuilder
from core.model.position import from_chess_notation
from core.model.piece import Color
from core.events.event_bus import Capture
from server.serializer import serialize, make_event_collector
from server.db import update_ratings, STARTING_RATING
from constants import DEFAULT_BOARD

ROWS = 8
DISCONNECT_TIMEOUT_S = 20


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
        self.ratings = {}   # {Color.WHITE: rating, Color.BLACK: rating}
        self._ratings_finalized = False
        self._initial_broadcast_sent = False
        self._disconnect_task = None
        self._disconnect_deadline = None
        self._resigned_color = None
        self.engine.start()

    def _winner_color(self):
        """Color of the player who wins: by resignation (disconnect timeout), else by king capture."""
        if self._resigned_color is not None:
            return Color.BLACK if self._resigned_color == Color.WHITE else Color.WHITE
        for e in self.events:
            if isinstance(e, Capture) and e.captured_piece.is_king:
                return e.capturing_color
        return None

    def handle_disconnect(self, color: Color):
        """Start a DISCONNECT_TIMEOUT_S countdown; the opponent auto-wins if it elapses."""
        if self.engine.state.game_over or self._disconnect_task is not None:
            return
        self._disconnect_deadline = time.monotonic() + DISCONNECT_TIMEOUT_S
        self._disconnect_task = asyncio.create_task(self._resign_after_timeout(color))

    async def _resign_after_timeout(self, disconnected_color: Color):
        await asyncio.sleep(DISCONNECT_TIMEOUT_S)
        if self.engine.state.game_over:
            return
        self._resigned_color = disconnected_color
        self.engine.force_game_over()
        survivor = Color.BLACK if disconnected_color == Color.WHITE else Color.WHITE
        try:
            await self.send_state(self.sockets[survivor])
        except Exception:
            pass

    def disconnect_seconds_left(self):
        """Seconds left before an auto-resign, or None if no disconnect is in progress."""
        if self._disconnect_deadline is None or self.engine.state.game_over:
            return None
        return max(0, round(self._disconnect_deadline - time.monotonic()))

    def _finalize_ratings(self):
        """Apply and persist the ELO update once, the moment the game ends."""
        if self._ratings_finalized or not self.engine.state.game_over:
            return
        self._ratings_finalized = True
        winner = self._winner_color()
        if winner is None:
            return
        result = "white" if winner == Color.WHITE else "black"
        new_white, new_black = update_ratings(self.names[Color.WHITE], self.names[Color.BLACK], result)
        self.ratings[Color.WHITE] = new_white
        self.ratings[Color.BLACK] = new_black

    async def send_state(self, ws):
        await ws.send(serialize(self.engine.board, self.engine.state, self.events,
                                white_name=self.names.get(Color.WHITE, "White"),
                                black_name=self.names.get(Color.BLACK, "Black"),
                                white_rating=self.ratings.get(Color.WHITE, STARTING_RATING),
                                black_rating=self.ratings.get(Color.BLACK, STARTING_RATING),
                                disconnect_seconds_left=self.disconnect_seconds_left()))

    async def send_initial_broadcast(self):
        """
        Send the first post-match state to both players exactly once.
        Both players' handle() coroutines reach this point independently right
        after matching, so sending+clearing events per-connection (like a plain
        send_state does) races: whichever coroutine runs second would find
        events (e.g. GameStarted) already cleared by the first. Guarding with a
        flag and using broadcast() (send-to-both-then-clear-once) avoids that.
        """
        if self._initial_broadcast_sent:
            return
        self._initial_broadcast_sent = True
        await self.broadcast()

    async def broadcast(self):
        self._finalize_ratings()
        for ws in self.sockets.values():
            try:
                await self.send_state(ws)
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

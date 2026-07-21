import asyncio
from core.model.piece import Color
from server.game_session import GameSession
from logger import logger


class Matchmaker:
    """Pairs two connecting sockets into a single GameSession (one match at a time)."""

    def __init__(self):
        self._waiting = None  # (ws, username, session, asyncio.Event)

    async def join(self, ws, username: str, rating: int) -> tuple[Color, GameSession]:
        if self._waiting is None:
            session = GameSession()
            session.names[Color.WHITE] = username
            session.sockets[Color.WHITE] = ws
            session.ratings[Color.WHITE] = rating
            ready = asyncio.Event()
            self._waiting = (ws, username, session, ready)
            logger.info("[lobby] %s joined as White — waiting for Black...", username)
            await ws.send("WAITING")
            await ready.wait()
            return Color.WHITE, session

        _ws1, _name1, session, ready = self._waiting
        self._waiting = None
        session.names[Color.BLACK] = username
        session.sockets[Color.BLACK] = ws
        session.ratings[Color.BLACK] = rating
        logger.info("[lobby] %s joined as Black — starting game!", username)
        ready.set()
        return Color.BLACK, session

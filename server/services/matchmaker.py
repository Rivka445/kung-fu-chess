import asyncio
from dataclasses import dataclass
from shared.model.piece import Color
from server.game.session import GameSession
from shared.helpers.logger import logger

RATING_RANGE = 100
SEARCH_TIMEOUT_S = 60


@dataclass
class _WaitingPlayer:
    ws: object
    username: str
    rating: int
    session: GameSession
    ready: asyncio.Event


class Matchmaker:
    """Pairs waiting sockets into a GameSession, matching only within ±RATING_RANGE ELO."""

    def __init__(self):
        self._waiting: list[_WaitingPlayer] = []

    async def join(self, ws, username: str, rating: int) -> tuple[Color, GameSession]:
        for i, w in enumerate(self._waiting):
            if abs(w.rating - rating) <= RATING_RANGE:
                self._waiting.pop(i)
                session = w.session
                session.names[Color.BLACK] = username
                session.sockets[Color.BLACK] = ws
                session.ratings[Color.BLACK] = rating
                logger.info("[lobby] %s (rating %d) matched with %s (rating %d)",
                            username, rating, w.username, w.rating)
                w.ready.set()
                return Color.BLACK, session

        session = GameSession()
        session.names[Color.WHITE] = username
        session.sockets[Color.WHITE] = ws
        session.ratings[Color.WHITE] = rating
        entry = _WaitingPlayer(ws, username, rating, session, asyncio.Event())
        self._waiting.append(entry)
        logger.info("[lobby] %s (rating %d) joined queue — waiting for a match...", username, rating)
        try:
            await entry.ready.wait()
        finally:
            if entry in self._waiting:
                self._waiting.remove(entry)
        return Color.WHITE, session

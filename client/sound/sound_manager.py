import queue
import threading
from pathlib import Path
from playsound import playsound
from shared.events.event_bus import EventBus, MoveApplied, Capture, GameOver
from shared.helpers.logger import logger

_DIR = Path(__file__).parent

# Concurrent playsound() calls from separate threads race on Windows' MCI
# backend (mciSendStringA) and one silently fails to open — e.g. a capture
# fires "click" and "eat" at nearly the same instant and only one plays.
# A single worker draining a queue keeps every playsound() call sequential.
_queue: "queue.Queue[str]" = queue.Queue()


def _worker():
    while True:
        file = _queue.get()
        try:
            playsound(str(_DIR / file))
        except Exception:
            logger.exception("failed to play sound %s", file)


threading.Thread(target=_worker, daemon=True).start()


def _play(file: str):
    _queue.put(file)


class SoundManager:
    def __init__(self, bus: EventBus):
        bus.subscribe(MoveApplied, lambda e: _play("click.mp3"))
        bus.subscribe(Capture,     lambda e: _play("eat.mp3"))
        bus.subscribe(GameOver,    lambda e: _play("game over.mp3"))

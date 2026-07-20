import threading
from pathlib import Path
from playsound import playsound
from core.events.event_bus import EventBus, MoveApplied, Capture, KingCaptured

_DIR = Path(__file__).parent


def _play(file: str):
    threading.Thread(target=playsound, args=(str(_DIR / file),), daemon=True).start()


class SoundManager:
    def __init__(self, bus: EventBus):
        bus.subscribe(MoveApplied,   lambda e: _play("click.mp3"))
        bus.subscribe(Capture,       lambda e: _play("eat.mp3"))
        bus.subscribe(KingCaptured,  lambda e: _play("game over.mp3"))

import threading
from pathlib import Path
from playsound import playsound
from core.events.base import GameEventListener
from core.model.position import Position

_DIR = Path(__file__).parent


def _play(file: str):
    threading.Thread(target=playsound, args=(str(_DIR / file),), daemon=True).start()


class SoundManager(GameEventListener):
    def on_move_applied(self, source: Position, target: Position):
        _play("click.mp3")

    def on_capture(self, captured_piece, capturing_color):
        _play("eat.mp3")

    def on_king_captured(self, pos: Position):
        _play("game over.mp3")

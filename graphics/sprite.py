import json
import pathlib
from graphics.img import Img
from constants import MOVE_DURATION

PIECES_DIR = pathlib.Path(__file__).parent.parent / "assets" / "assets" / "images" / "pieces"

# Maps (piece_type_char, color_char) -> folder name  e.g. ('P','W') -> 'PW'
# piece type chars match PieceType.value: K Q R B N P
# color chars match Color.value: w b  -> we uppercase for folder name


def _folder(piece) -> str:
    return piece.type.value + piece.color.value.upper()


def _load_state(piece_folder: pathlib.Path, state: str) -> tuple[list[Img], float, bool]:
    """Load sprites and config for a given state. Returns (frames, fps, is_loop)."""
    state_dir = piece_folder / "states" / state
    config = json.loads((state_dir / "config.json").read_text())
    fps = config["graphics"]["frames_per_sec"]
    is_loop = config["graphics"]["is_loop"]

    sprites_dir = state_dir / "sprites"
    frames = []
    for i in range(1, 6):
        p = sprites_dir / f"{i}.png"
        if p.exists():
            frames.append(Img().read(str(p), size=(100, 100), keep_aspect=True))
    return frames, fps, is_loop


class SpriteSheet:
    """Holds all animation states for one piece type."""

    def __init__(self, piece):
        folder = PIECES_DIR / _folder(piece)
        self._states: dict[str, tuple[list[Img], float, bool]] = {}
        for state in ("idle", "move", "jump", "short_rest", "long_rest"):
            self._states[state] = _load_state(folder, state)

    def get_frame(self, state: str, time_ms: int, state_start_ms: int = 0) -> Img:
        frames, fps, is_loop = self._states[state]
        total = len(frames)
        elapsed = time_ms - state_start_ms
        frame_duration_ms = 1000 / fps
        index = int(elapsed / frame_duration_ms)
        if is_loop:
            index = index % total
        else:
            index = min(index, total - 1)
        return frames[index]


# Cache so we don't reload from disk every frame
_cache: dict[str, SpriteSheet] = {}


def get_sprite_sheet(piece) -> SpriteSheet:
    key = _folder(piece)
    if key not in _cache:
        _cache[key] = SpriteSheet(piece)
    return _cache[key]


def piece_state(pos, game_state) -> str:
    """Map GameState status at pos to a sprite state name."""
    from model.piece_status import IdleStatus, InFlightStatus, OnCooldownStatus
    status = game_state.get_status(pos)
    if isinstance(status, InFlightStatus):
        # airborne = jump, pending move = move
        if any(a.cell == pos for a in game_state.airborne):
            return "jump"
        return "move"
    if isinstance(status, OnCooldownStatus):
        cooldown_remaining = status._until - game_state.current_time
        return "long_rest" if cooldown_remaining > MOVE_DURATION else "short_rest"
    return "idle"

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.model.piece import Piece, PieceType, Color
from shared.model.position import Position
from shared.model.game_state import GameState, PendingMove, AirbornePiece
from shared.constants.constants import MOVE_DURATION
from client.graphics import sprite as sprite_module
from client.graphics.sprite import get_sprite_sheet, piece_state, SpriteSheet


KING_WHITE = Piece(Color.WHITE, PieceType.KING)


def test_get_sprite_sheet_is_cached_per_piece_type():
    sheet_a = get_sprite_sheet(KING_WHITE)
    sheet_b = get_sprite_sheet(Piece(Color.WHITE, PieceType.KING))
    assert sheet_a is sheet_b
    assert isinstance(sheet_a, SpriteSheet)


def test_get_sprite_sheet_different_piece_types_differ():
    king_sheet = get_sprite_sheet(KING_WHITE)
    queen_sheet = get_sprite_sheet(Piece(Color.WHITE, PieceType.QUEEN))
    assert king_sheet is not queen_sheet


def test_get_frame_resizes_to_requested_cell_size():
    sheet = get_sprite_sheet(KING_WHITE)
    frame = sheet.get_frame("idle", time_ms=0, state_start_ms=0, cell_size=64)
    assert frame.img.shape == (64, 64, 4)


def test_get_frame_loop_state_advances_and_wraps():
    # idle: fps=4 (250ms/frame), is_loop=True, 5 frames.
    sheet = get_sprite_sheet(KING_WHITE)
    f0 = sheet.get_frame("idle", time_ms=0, state_start_ms=0, cell_size=20)
    f2 = sheet.get_frame("idle", time_ms=600, state_start_ms=0, cell_size=20)
    f_wrapped = sheet.get_frame("idle", time_ms=1300, state_start_ms=0, cell_size=20)
    # Frame at 1300ms (index 5 -> wraps to 0) should match frame at time 0.
    assert (f_wrapped.img == f0.img).all()
    assert not (f2.img == f0.img).all()


def test_get_frame_non_loop_state_clamps_at_last_frame():
    # jump: fps=10 (100ms/frame), is_loop=False, 5 frames -> clamps after 400ms.
    sheet = get_sprite_sheet(KING_WHITE)
    last = sheet.get_frame("jump", time_ms=400, state_start_ms=0, cell_size=20)
    way_past = sheet.get_frame("jump", time_ms=5000, state_start_ms=0, cell_size=20)
    assert (last.img == way_past.img).all()


def test_piece_state_idle_by_default():
    state = GameState()
    pos = Position(0, 0)
    assert piece_state(pos, state) == "idle"


def test_piece_state_move_for_pending_source():
    state = GameState()
    pos = Position(0, 0)
    state.pending_moves.append(PendingMove(pos, Position(0, 2), arrival=2000))
    assert piece_state(pos, state) == "move"


def test_piece_state_jump_for_airborne():
    state = GameState()
    pos = Position(1, 1)
    state.airborne.append(AirbornePiece(pos, landing_time=1000))
    assert piece_state(pos, state) == "jump"


def test_piece_state_short_and_long_rest_by_remaining_cooldown():
    pos = Position(2, 2)

    long_rest_state = GameState(current_time=0)
    long_rest_state.cooldowns[pos] = MOVE_DURATION * 2
    assert piece_state(pos, long_rest_state) == "long_rest"

    short_rest_state = GameState(current_time=MOVE_DURATION * 2 - MOVE_DURATION // 2)
    short_rest_state.cooldowns[pos] = MOVE_DURATION * 2
    assert piece_state(pos, short_rest_state) == "short_rest"

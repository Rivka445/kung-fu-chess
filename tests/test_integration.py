import sys
import io

import pytest
from io import StringIO
from script_test.script_runner import run


def run_script(script: str) -> str:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        run(StringIO(script))
    except SystemExit:
        pass
    finally:
        sys.stdout = old
    return buf.getvalue().strip()


# --- Board parsing ---

def test_parse_rectangular_board_3x4():
    out = run_script("Board:\nwK . . bK\n. . . .\nwR . . bR\nCommands:\nprint board\n")
    assert out == "wK . . bK\n. . . .\nwR . . bR"


def test_parse_piece_tokens_and_colors():
    out = run_script("Board:\nwK . bQ\n. wN .\nbP . wR\nCommands:\nprint board\n")
    assert out == "wK . bQ\n. wN .\nbP . wR"


def test_reject_unknown_token():
    out = run_script("Board:\nwK xZ\n. .\nCommands:\n")
    assert out == "ERROR UNKNOWN_TOKEN"


def test_reject_row_width_mismatch():
    out = run_script("Board:\nwK . .\n. bK\nCommands:\n")
    assert out == "ERROR ROW_WIDTH_MISMATCH"


# --- Click / selection ---

def test_select_piece_by_center_click():
    out = run_script("Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board\n")
    assert out == ". . .\n. wK .\n. . ."


def test_click_empty_cell_does_not_select():
    out = run_script("Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 150 150\nclick 250 250\nwait 1000\nprint board\n")
    assert out == "wK . .\n. . .\n. . ."


def test_click_outside_board_is_ignored():
    out = run_script("Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 350 50\nclick -10 50\nprint board\n")
    assert out == "wK . .\n. . .\n. . ."


def test_clicking_another_piece_replaces_selection():
    out = run_script("Board:\nwR . wK\n. . .\nCommands:\nclick 50 50\nclick 250 50\nclick 250 150\nwait 1000\nprint board\n")
    assert out == "wR . .\n. . wK"


def test_reject_unknown_token_with_print():
    out = run_script("Board:\nwK xZ\n. .\nCommands:\nprint board\n")
    assert out == "ERROR UNKNOWN_TOKEN"


def test_reject_row_width_mismatch_with_print():
    out = run_script("Board:\nwK . .\n. bK\nCommands:\nprint board\n")
    assert out == "ERROR ROW_WIDTH_MISMATCH"


# --- Piece movement rules ---

def test_king_one_step_valid():
    out = run_script("Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board\n")
    assert out == ". . .\n. wK .\n. . ."


def test_king_two_steps_invalid():
    out = run_script("Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 1000\nprint board\n")
    assert out == "wK . .\n. . .\n. . ."


def test_rook_straight_valid():
    out = run_script("Board:\nwR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board\n")
    assert out == ". . wR"


def test_rook_diagonal_invalid():
    out = run_script("Board:\nwR . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board\n")
    assert out == "wR . .\n. . .\n. . ."


def test_bishop_diagonal_valid():
    out = run_script("Board:\nwB . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board\n")
    assert out == ". . .\n. . .\n. . wB"


def test_knight_L_valid():
    out = run_script("Board:\nwN . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 250\nwait 3000\nprint board\n")
    assert out == ". . .\n. . .\n. wN ."


def test_queen_diagonal_valid():
    out = run_script("Board:\nwQ . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board\n")
    assert out == ". . .\n. . .\n. . wQ"


def test_rook_blocked_by_own_piece():
    out = run_script("Board:\nwR wP .\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board\n")
    assert out == "wR wP ."


def test_bishop_blocked_by_own_piece():
    out = run_script("Board:\nwB . .\n. wP .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board\n")
    assert out == "wB . .\n. wP .\n. . ."


def test_knight_jumps_over_blockers():
    out = run_script("Board:\nwN wP .\nwP . .\n. . .\nCommands:\nclick 50 50\nclick 150 250\nwait 3000\nprint board\n")
    assert out == ". wP .\nwP . .\n. wN ."


# --- Pawn double-step (Tests 39, 40, 42) ---

def test_pawn_double_step_from_start_row_white():
    # Test 39: 5-row board, white pawn at row3 (start_row = len-2 = 3), moves 2 steps to row1
    out = run_script(
        "Board:\n. . .\n. . .\n. . .\n. wP .\n. . .\n"
        "Commands:\nclick 150 350\nclick 150 150\nwait 2000\nprint board\n"
    )
    assert out == ". . .\n. wP .\n. . .\n. . .\n. . ."


def test_pawn_double_step_from_start_row_black():
    # Test 40: 5-row board, black pawn at row1 (start_row = 1), moves 2 steps to row3
    out = run_script(
        "Board:\n. . .\n. bP .\n. . .\n. . .\n. . .\n"
        "Commands:\nclick 150 150\nclick 150 350\nwait 2000\nprint board\n"
    )
    assert out == ". . .\n. . .\n. . .\n. bP .\n. . ."


def test_pawn_double_step_not_from_start_row_illegal():
    # Test 42: 4-row board, white pawn at row3 (start_row = len-2 = 2), pawn at row3 != 2 -> illegal
    out = run_script(
        "Board:\n. . .\n. . .\n. . .\n. wP .\n"
        "Commands:\nclick 150 350\nclick 150 150\nwait 2000\nprint board\n"
    )
    assert out == ". . .\n. . .\n. . .\n. wP ."


# --- Pawn promotion (Test 45) ---

def test_promoted_pawn_moves_as_queen():
    # Test 45: 3-row board, white pawn at row1 (start_row = len-2 = 1)
    # Pawn moves 1 step to row0 -> promotes to wQ (distance=1, arrival=1000ms)
    # Queen is on cooldown until 2000ms — wait for cooldown then move diagonally
    out = run_script(
        "Board:\n. . .\n. wP .\n. . .\n"
        "Commands:\nclick 150 150\nclick 150 50\nwait 2000\nclick 150 50\nclick 250 150\nwait 1000\nprint board\n"
    )
    assert out == ". . .\n. . wQ\n. . ."

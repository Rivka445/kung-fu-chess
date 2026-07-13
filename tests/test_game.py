import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.position import Position
from model.piece import Piece
from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine
from engine.game_engine import GameEngine
from input.controller import Controller


def make_game(rows):
    board = Board()
    for row in rows:
        board.add_parsed_row(parse_row(row, board.expected_cols))
    engine = GameEngine(board, RuleEngine())
    controller = Controller(engine)
    return engine, controller, board


def test_click_selects_piece():
    engine, controller, _ = make_game(["wR . ."])
    controller.click(50, 50, 100)
    assert controller._selected == Position(0, 0)


def test_click_moves_piece_to_pending():
    engine, controller, _ = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 1


def test_piece_not_arrived_before_wait():
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    engine.advance_time(500)
    assert board.get_piece(Position(0, 0)) == Piece.from_str("wR")


def test_piece_arrives_after_wait():
    # col0->col2 = distance 2, arrival = 2000ms
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    engine.advance_time(2000)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert board.get_piece(Position(0, 0)) is None


def test_busy_piece_cannot_move_again():
    engine, controller, _ = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 1


def test_illegal_move_not_added():
    engine, controller, _ = make_game(["wB . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 0


def test_same_color_cannot_capture():
    engine, controller, _ = make_game(["wR wK ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    assert len(engine.state.pending_moves) == 0


def test_blocked_rook_cannot_move():
    engine, controller, _ = make_game(["wR bP ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 0


def test_click_outside_board_ignored():
    engine, controller, _ = make_game(["wR . ."])
    controller.click(9999, 9999, 100)
    assert controller._selected is None


def test_jump_adds_airborne():
    engine, controller, _ = make_game([". . .", ". wK .", ". . ."])
    controller.jump(150, 150, 100)
    assert len(engine.state.airborne) == 1


def test_airborne_piece_lands_no_enemy():
    engine, controller, board = make_game([". . .", ". wK .", ". . ."])
    controller.jump(150, 150, 100)
    engine.advance_time(1000)
    assert board.get_piece(Position(1, 1)) == Piece.from_str("wK")


def test_airborne_captures_arriving_enemy():
    # bR moves col2->col0 = distance 2, arrival=2000ms
    engine, controller, board = make_game([". . .", "wK . bR", ". . ."])
    controller.jump(50, 150, 100)
    controller.click(250, 150, 100)
    controller.click(50, 150, 100)
    engine.advance_time(2000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("wK")
    assert board.get_piece(Position(1, 2)) is None


def test_jump_too_late_does_not_save():
    # bR moves col2->col0 = distance 2, arrival=2000ms
    engine, controller, board = make_game([". . .", "wK . bR", ". . ."])
    controller.click(250, 150, 100)
    controller.click(50, 150, 100)
    engine.advance_time(2000)
    controller.jump(50, 150, 100)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("bR")


def test_cannot_jump_while_moving():
    # col0->col2 = distance 2, arrival=2000ms; advance 500 then jump, then 2000 more
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    engine.advance_time(500)
    controller.jump(50, 50, 100)
    engine.advance_time(2000)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert len(engine.state.airborne) == 0


def test_airborne_does_not_capture_same_color():
    # wR moves col2->col0 = distance 2, arrival=2000ms
    engine, controller, board = make_game([". . .", "wK . wR", ". . ."])
    controller.jump(50, 150, 100)
    controller.click(250, 150, 100)
    controller.click(50, 150, 100)
    engine.advance_time(2000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("wK")
    assert board.get_piece(Position(1, 2)) == Piece.from_str("wR")


def test_enemy_arrives_after_landing_captures_normally():
    # bR moves col3->col0 = distance 3, arrival=3000ms
    engine, controller, board = make_game([". . . .", "wK . . bR", ". . . ."])
    controller.jump(50, 150, 100)
    engine.advance_time(1000)
    controller.click(350, 150, 100)
    controller.click(50, 150, 100)
    engine.advance_time(3000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("bR")


def test_two_rooks_same_columns_both_move():
    # col0->col2 = distance 2, arrival=2000ms
    engine, controller, board = make_game(["wR . .", ". . .", "bR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    controller.click(50, 250, 100)
    controller.click(250, 250, 100)
    engine.advance_time(2000)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert board.get_piece(Position(2, 2)) == Piece.from_str("bR")


# --- Real-time: mid-flight and cooldown (Tests 26, 29, 30, 31, 32) ---

def test_piece_still_at_source_mid_flight():
    # Test 26: col0->col2 takes 2000ms; at 1000ms piece still at source
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(250, 50, 100)
    engine.advance_time(1000)
    assert board.get_piece(Position(0, 0)) == Piece.from_str("wR")
    assert board.get_piece(Position(0, 2)) is None


def test_piece_arrives_exactly_at_move_duration():
    # Test 29: col0->col1 = distance 1, arrives at exactly 1000ms
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    engine.advance_time(1000)
    assert board.get_piece(Position(0, 1)) == Piece.from_str("wR")
    assert board.get_piece(Position(0, 0)) is None


def test_piece_can_move_again_after_landing():
    # Test 30: no cooldown on regular moves — piece can move again immediately after landing
    engine, controller, board = make_game(["wR . . ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    engine.advance_time(1000)
    controller.click(150, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 1


def test_piece_can_move_after_cooldown_expires():
    # Test 31: piece can move again after landing (no cooldown)
    engine, controller, board = make_game(["wR . . ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    engine.advance_time(1000)
    engine.advance_time(1000)
    controller.click(150, 50, 100)
    controller.click(250, 50, 100)
    assert len(engine.state.pending_moves) == 1


def test_piece_not_at_target_before_arrival():
    # Test 32: col0->col1 = 1000ms; at 500ms target is still empty
    engine, controller, board = make_game(["wR . ."])
    controller.click(50, 50, 100)
    controller.click(150, 50, 100)
    engine.advance_time(500)
    assert board.get_piece(Position(0, 1)) is None

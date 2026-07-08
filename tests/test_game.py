import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.position import Position
from models.piece import Piece
from services.board import ChessBoard
from services.board_parser import parse_row
from services.move_rules import Rules
from controllers.game_controller import Game


def make_game(rows):
    board = ChessBoard()
    for row in rows:
        board.add_parsed_row(parse_row(row))
    return Game(board, Rules()), board


def test_click_selects_piece():
    game, _ = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    assert game.state.selected == Position(0, 0)


def test_click_moves_piece_to_pending():
    game, _ = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    assert len(game.state.pending_moves) == 1


def test_piece_not_arrived_before_wait():
    game, board = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    game.handle_wait(500)
    assert board.get_piece(Position(0, 0)) == Piece.from_str("wR")


def test_piece_arrives_after_wait():
    game, board = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    game.handle_wait(1000)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert board.get_piece(Position(0, 0)) is None


def test_busy_piece_cannot_move_again():
    game, _ = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(150, 50, 100)
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    assert len(game.state.pending_moves) == 1


def test_illegal_move_not_added():
    game, _ = make_game(["wB . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    assert len(game.state.pending_moves) == 0


def test_same_color_cannot_capture():
    game, _ = make_game(["wR wK ."])
    game.handle_click(50, 50, 100)
    game.handle_click(150, 50, 100)
    assert len(game.state.pending_moves) == 0


def test_blocked_rook_cannot_move():
    game, _ = make_game(["wR bP ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    assert len(game.state.pending_moves) == 0


def test_click_outside_board_ignored():
    game, _ = make_game(["wR . ."])
    game.handle_click(9999, 9999, 100)
    assert game.state.selected is None


def test_jump_adds_airborne():
    game, _ = make_game([". . .", ". wK .", ". . ."])
    game.handle_jump(150, 150, 100)
    assert len(game.state.airborne) == 1


def test_airborne_piece_lands_no_enemy():
    game, board = make_game([". . .", ". wK .", ". . ."])
    game.handle_jump(150, 150, 100)
    game.handle_wait(1000)
    assert board.get_piece(Position(1, 1)) == Piece.from_str("wK")


def test_airborne_captures_arriving_enemy():
    game, board = make_game([". . .", "wK . bR", ". . ."])
    game.handle_jump(50, 150, 100)
    game.handle_click(250, 150, 100)
    game.handle_click(50, 150, 100)
    game.handle_wait(1000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("wK")
    assert board.get_piece(Position(1, 2)) is None


def test_jump_too_late_does_not_save():
    game, board = make_game([". . .", "wK . bR", ". . ."])
    game.handle_click(250, 150, 100)
    game.handle_click(50, 150, 100)
    game.handle_wait(1000)
    game.handle_jump(50, 150, 100)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("bR")


def test_cannot_jump_while_moving():
    game, board = make_game(["wR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    game.handle_wait(500)
    game.handle_jump(50, 50, 100)
    game.handle_wait(1500)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert len(game.state.airborne) == 0


def test_airborne_does_not_capture_same_color():
    game, board = make_game([". . .", "wK . wR", ". . ."])
    game.handle_jump(50, 150, 100)
    game.handle_click(250, 150, 100)
    game.handle_click(50, 150, 100)
    game.handle_wait(1000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("wK")
    assert board.get_piece(Position(1, 2)) == Piece.from_str("wR")


def test_enemy_arrives_after_landing_captures_normally():
    game, board = make_game([". . . .", "wK . . bR", ". . . ."])
    game.handle_jump(50, 150, 100)
    game.handle_wait(1000)
    game.handle_click(350, 150, 100)
    game.handle_click(50, 150, 100)
    game.handle_wait(3000)
    assert board.get_piece(Position(1, 0)) == Piece.from_str("bR")


def test_two_rooks_same_columns_both_move():
    game, board = make_game(["wR . .", ". . .", "bR . ."])
    game.handle_click(50, 50, 100)
    game.handle_click(250, 50, 100)
    game.handle_click(50, 250, 100)
    game.handle_click(250, 250, 100)
    game.handle_wait(2000)
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")
    assert board.get_piece(Position(2, 2)) == Piece.from_str("bR")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.piece import Piece, Color, PieceType
from models.position import Position
from services.board import ChessBoard
from services.board_parser import parse_row


def make_board(rows):
    board = ChessBoard()
    for row in rows:
        board.add_parsed_row(parse_row(row))
    return board


def test_is_inside_valid():
    assert make_board(["wR . ."]).is_inside(Position(0, 0))


def test_is_inside_out_of_row():
    assert not make_board(["wR . ."]).is_inside(Position(1, 0))


def test_is_inside_out_of_col():
    assert not make_board(["wR . ."]).is_inside(Position(0, 3))


def test_get_piece():
    board = make_board(["wR . ."])
    assert board.get_piece(Position(0, 0)) == Piece.from_str("wR")
    assert board.get_piece(Position(0, 1)) is None


def test_move_piece():
    board = make_board(["wR . ."])
    board.move_piece(Position(0, 0), Position(0, 2))
    assert board.get_piece(Position(0, 0)) is None
    assert board.get_piece(Position(0, 2)) == Piece.from_str("wR")


def test_remove_piece():
    board = make_board(["wR . ."])
    board.remove_piece(Position(0, 0))
    assert board.get_piece(Position(0, 0)) is None


def test_has_blockers_true():
    assert make_board(["wR bP ."]).has_blockers(Position(0, 0), Position(0, 2))


def test_has_blockers_false():
    assert not make_board(["wR . ."]).has_blockers(Position(0, 0), Position(0, 2))


def test_promote_pawn_white():
    board = make_board(["wP . ."])
    board.promote_pawn(Position(0, 0))
    assert board.get_piece(Position(0, 0)) == Piece(Color.WHITE, PieceType.QUEEN)


def test_promote_pawn_not_last_row():
    board = make_board([". . .", "wP . ."])
    board.promote_pawn(Position(1, 0))
    assert board.get_piece(Position(1, 0)) == Piece.from_str("wP")


def test_promote_pawn_black():
    board = make_board([". . .", "bP . ."])
    board.promote_pawn(Position(1, 0))
    assert board.get_piece(Position(1, 0)) == Piece(Color.BLACK, PieceType.QUEEN)


def test_same_color_true():
    board = make_board(["wR wK ."])
    assert board.same_color(Piece.from_str("wR"), Piece.from_str("wK"))


def test_same_color_false():
    assert not make_board(["."]).same_color(Piece.from_str("wR"), Piece.from_str("bK"))


def test_same_color_none():
    assert not make_board(["."]).same_color(None, Piece.from_str("wK"))

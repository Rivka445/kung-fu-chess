import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.piece import Piece
from models.position import Position
from services.rules import Rules

rules = Rules()


def p(s): return Piece.from_str(s)
def pos(r, c): return Position(r, c)


def test_rook_horizontal(): assert rules.is_legal_move(p("wR"), pos(0, 0), pos(0, 3))
def test_rook_vertical(): assert rules.is_legal_move(p("wR"), pos(0, 0), pos(3, 0))
def test_rook_diagonal_illegal(): assert not rules.is_legal_move(p("wR"), pos(0, 0), pos(2, 2))
def test_bishop_diagonal(): assert rules.is_legal_move(p("wB"), pos(0, 0), pos(3, 3))
def test_bishop_straight_illegal(): assert not rules.is_legal_move(p("wB"), pos(0, 0), pos(0, 3))
def test_queen_straight(): assert rules.is_legal_move(p("wQ"), pos(0, 0), pos(0, 4))
def test_queen_diagonal(): assert rules.is_legal_move(p("wQ"), pos(0, 0), pos(3, 3))
def test_knight_valid(): assert rules.is_legal_move(p("wN"), pos(0, 0), pos(2, 1))
def test_knight_valid2(): assert rules.is_legal_move(p("wN"), pos(0, 0), pos(1, 2))
def test_knight_invalid(): assert not rules.is_legal_move(p("wN"), pos(0, 0), pos(2, 2))
def test_king_one_step(): assert rules.is_legal_move(p("wK"), pos(0, 0), pos(1, 1))
def test_king_two_steps_illegal(): assert not rules.is_legal_move(p("wK"), pos(0, 0), pos(2, 0))
def test_no_move(): assert not rules.is_legal_move(p("wR"), pos(0, 0), pos(0, 0))

def test_white_forward(): assert rules.is_legal_pawn_move(p("wP"), pos(4, 0), pos(3, 0), None)
def test_white_forward_blocked(): assert not rules.is_legal_pawn_move(p("wP"), pos(4, 0), pos(3, 0), p("bP"))
def test_white_double_from_start(): assert rules.is_legal_pawn_move(p("wP"), pos(7, 0), pos(5, 0), None, board_rows=8)
def test_white_double_not_from_start(): assert not rules.is_legal_pawn_move(p("wP"), pos(4, 0), pos(2, 0), None, board_rows=8)
def test_white_capture(): assert rules.is_legal_pawn_move(p("wP"), pos(4, 1), pos(3, 2), p("bP"))
def test_white_capture_empty(): assert not rules.is_legal_pawn_move(p("wP"), pos(4, 1), pos(3, 2), None)
def test_black_forward(): assert rules.is_legal_pawn_move(p("bP"), pos(1, 0), pos(2, 0), None)
def test_black_double_from_start(): assert rules.is_legal_pawn_move(p("bP"), pos(0, 0), pos(2, 0), None, board_rows=8)
def test_white_backward_illegal(): assert not rules.is_legal_pawn_move(p("wP"), pos(4, 0), pos(5, 0), None)

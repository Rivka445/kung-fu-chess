import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.piece import Piece, Color, PieceType
from model.position import Position
from model.board import Board
from board_io.board_parser import parse_row
from rules.rule_engine import RuleEngine

engine = RuleEngine()


def p(s): return Piece.from_str(s)
def pos(r, c): return Position(r, c)


def make_board(rows):
    board = Board()
    for row in rows:
        board.add_parsed_row(parse_row(row, board.expected_cols))
    return board


# empty board stub for shape-only tests
_empty = make_board([". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . .",
                     ". . . . . . . ."])


def test_rook_horizontal(): assert engine.is_legal(p("wR"), pos(0, 0), pos(0, 3), _empty)
def test_rook_vertical(): assert engine.is_legal(p("wR"), pos(0, 0), pos(3, 0), _empty)
def test_rook_diagonal_illegal(): assert not engine.is_legal(p("wR"), pos(0, 0), pos(2, 2), _empty)
def test_bishop_diagonal(): assert engine.is_legal(p("wB"), pos(0, 0), pos(3, 3), _empty)
def test_bishop_straight_illegal(): assert not engine.is_legal(p("wB"), pos(0, 0), pos(0, 3), _empty)
def test_queen_straight(): assert engine.is_legal(p("wQ"), pos(0, 0), pos(0, 4), _empty)
def test_queen_diagonal(): assert engine.is_legal(p("wQ"), pos(0, 0), pos(3, 3), _empty)
def test_knight_valid(): assert engine.is_legal(p("wN"), pos(0, 0), pos(2, 1), _empty)
def test_knight_valid2(): assert engine.is_legal(p("wN"), pos(0, 0), pos(1, 2), _empty)
def test_knight_invalid(): assert not engine.is_legal(p("wN"), pos(0, 0), pos(2, 2), _empty)
def test_king_one_step(): assert engine.is_legal(p("wK"), pos(0, 0), pos(1, 1), _empty)
def test_king_two_steps_illegal(): assert not engine.is_legal(p("wK"), pos(0, 0), pos(2, 0), _empty)
def test_no_move(): assert not engine.is_legal(p("wR"), pos(0, 0), pos(0, 0), _empty)

def test_white_forward(): assert engine.is_legal(p("wP"), pos(4, 0), pos(3, 0), make_board([". . . . . . . .",
                                                                                            ". . . . . . . .",
                                                                                            ". . . . . . . .",
                                                                                            ". . . . . . . .",
                                                                                            "wP . . . . . . .",
                                                                                            ". . . . . . . .",
                                                                                            ". . . . . . . .",
                                                                                            ". . . . . . . ."]))
def test_white_forward_blocked():
    b = make_board([". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    "bP . . . . . . .",
                    "wP . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . ."])
    assert not engine.is_legal(p("wP"), pos(4, 0), pos(3, 0), b)

def test_white_double_from_start():
    b = make_board([". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    "wP . . . . . . .",
                    ". . . . . . . ."])
    assert engine.is_legal(p("wP"), pos(6, 0), pos(4, 0), b)

def test_white_double_not_from_start():
    b = make_board([". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    "wP . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . ."])
    assert not engine.is_legal(p("wP"), pos(4, 0), pos(2, 0), b)

def test_white_capture():
    b = make_board([". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". bP . . . . . .",
                    "wP . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . ."])
    assert engine.is_legal(p("wP"), pos(4, 0), pos(3, 1), b)

def test_white_capture_empty(): assert not engine.is_legal(p("wP"), pos(4, 1), pos(3, 2), _empty)

def test_black_forward():
    b = make_board([". . . . . . . .",
                    "bP . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . ."])
    assert engine.is_legal(p("bP"), pos(1, 0), pos(2, 0), b)

def test_black_double_from_start():
    b = make_board([". . . . . . . .",
                    "bP . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . ."])
    assert engine.is_legal(p("bP"), pos(1, 0), pos(3, 0), b)

def test_white_backward_illegal(): assert not engine.is_legal(p("wP"), pos(4, 0), pos(5, 0), _empty)

def test_white_double_blocked():
    b = make_board([". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    ". . . . . . . .",
                    "bP . . . . . . .",
                    "wP . . . . . . .",
                    ". . . . . . . ."])
    assert not engine.is_legal(p("wP"), pos(6, 0), pos(4, 0), b)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from shared.model.piece import Piece, Color, PieceType


def test_from_str():
    p = Piece.from_str("wK")
    assert p.color == Color.WHITE
    assert p.type == PieceType.KING


def test_to_str():
    assert Piece(Color.BLACK, PieceType.ROOK).to_str() == "bR"


def test_same_color_true():
    assert Piece.from_str("wK").same_color(Piece.from_str("wR"))


def test_same_color_false():
    assert not Piece.from_str("wK").same_color(Piece.from_str("bR"))


def test_is_king():
    assert Piece.from_str("wK").is_king
    assert not Piece.from_str("wR").is_king


def test_is_pawn():
    assert Piece.from_str("bP").is_pawn
    assert not Piece.from_str("bQ").is_pawn


def test_is_blockable():
    for t in ["wR", "wB", "wQ"]:
        assert Piece.from_str(t).is_blockable
    for t in ["wK", "wN", "wP"]:
        assert not Piece.from_str(t).is_blockable

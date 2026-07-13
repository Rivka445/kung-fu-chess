import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from model.piece import Piece
from board_io.board_parser import parse_row
from exceptions import EmptyRowError, RowWidthMismatchError, UnknownTokenError


def test_valid_row():
    row = parse_row("wR . bK", None)
    assert row[0] == Piece.from_str("wR")
    assert row[1] is None
    assert row[2] == Piece.from_str("bK")


def test_empty_row_raises():
    with pytest.raises(EmptyRowError):
        parse_row("", None)


def test_width_mismatch_raises():
    with pytest.raises(RowWidthMismatchError):
        parse_row("wR . bK", expected_cols=2)


def test_unknown_token_raises():
    with pytest.raises(UnknownTokenError):
        parse_row("wR XX bK", None)


def test_invalid_color_raises():
    with pytest.raises(UnknownTokenError):
        parse_row("xR . .", None)


def test_invalid_type_raises():
    with pytest.raises(UnknownTokenError):
        parse_row("wX . .", None)

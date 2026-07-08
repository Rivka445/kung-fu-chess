import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.piece import Piece
from services.board_parser import parse_row


def test_valid_row():
    row = parse_row("wR . bK")
    assert row[0] == Piece.from_str("wR")
    assert row[1] is None
    assert row[2] == Piece.from_str("bK")


def test_empty_row_raises():
    with pytest.raises(ValueError):
        parse_row("")


def test_width_mismatch_raises():
    with pytest.raises(ValueError):
        parse_row("wR . bK", expected_cols=2)


def test_unknown_token_raises():
    with pytest.raises(ValueError):
        parse_row("wR XX bK")


def test_invalid_color_raises():
    with pytest.raises(ValueError):
        parse_row("xR . .")


def test_invalid_type_raises():
    with pytest.raises(ValueError):
        parse_row("wX . .")

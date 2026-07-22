import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from shared.model.position import Position


def test_iter():
    row, col = Position(2, 3)
    assert (row, col) == (2, 3)


def test_equality():
    assert Position(1, 2) == Position(1, 2)
    assert Position(1, 2) != Position(2, 1)


def test_hashable():
    s = {Position(0, 0), Position(0, 0)}
    assert len(s) == 1

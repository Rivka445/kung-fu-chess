import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from shared.model.position import Position
from shared.model.game_state import GameState, PendingMove, AirbornePiece


def test_is_busy_pending():
    state = GameState()
    state.pending_moves.append(PendingMove(Position(0, 0), Position(0, 1), 1000))
    assert state.is_busy(Position(0, 0))
    assert not state.is_busy(Position(0, 1))


def test_is_busy_airborne():
    state = GameState()
    state.airborne.append(AirbornePiece(Position(1, 1), 500))
    assert state.is_busy(Position(1, 1))


def test_is_busy_cooldown_active():
    state = GameState(current_time=500)
    state.cooldowns[Position(2, 2)] = 1000
    assert state.is_busy(Position(2, 2))


def test_is_busy_cooldown_expired():
    state = GameState(current_time=2000)
    state.cooldowns[Position(2, 2)] = 1000
    assert not state.is_busy(Position(2, 2))


def test_not_busy_empty():
    assert not GameState().is_busy(Position(0, 0))

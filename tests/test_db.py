import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from server.db import authenticate_or_register, get_rating, update_ratings, AuthError, STARTING_RATING


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_chess.db")


def test_new_username_auto_registers_with_starting_rating(db_path):
    rating = authenticate_or_register("riki", "hunter2", db_path)
    assert rating == STARTING_RATING


def test_existing_username_correct_password_returns_rating(db_path):
    authenticate_or_register("riki", "hunter2", db_path)
    rating = authenticate_or_register("riki", "hunter2", db_path)
    assert rating == STARTING_RATING


def test_existing_username_wrong_password_raises(db_path):
    authenticate_or_register("riki", "hunter2", db_path)
    with pytest.raises(AuthError):
        authenticate_or_register("riki", "wrong-password", db_path)


def test_get_rating_unknown_user_raises(db_path):
    with pytest.raises(AuthError):
        get_rating("nobody", db_path)


def test_update_ratings_white_wins(db_path):
    authenticate_or_register("alice", "pw1", db_path)
    authenticate_or_register("bob", "pw2", db_path)

    new_white, new_black = update_ratings("alice", "bob", "white", db_path)

    assert new_white == 1216
    assert new_black == 1184
    assert get_rating("alice", db_path) == 1216
    assert get_rating("bob", db_path) == 1184


def test_update_ratings_persists_across_games(db_path):
    authenticate_or_register("alice", "pw1", db_path)
    authenticate_or_register("bob", "pw2", db_path)

    update_ratings("alice", "bob", "white", db_path)
    new_white, new_black = update_ratings("alice", "bob", "black", db_path)

    # alice (now 1216) loses to bob (now 1184) — alice drops further.
    assert new_white < 1216
    assert new_black > 1184

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from shared.model.piece import Color, Piece, PieceType
from shared.events.event_bus import Capture
from server.game.session import GameSession


def _make_session():
    session = GameSession()
    session.names[Color.WHITE] = "alice"
    session.names[Color.BLACK] = "bob"
    session.ratings[Color.WHITE] = 1200
    session.ratings[Color.BLACK] = 1200
    return session


def test_no_rating_change_while_game_in_progress():
    session = _make_session()
    with patch("server.game.session.update_ratings") as mock_update:
        session._finalize_ratings()
    mock_update.assert_not_called()


def test_non_king_capture_does_not_end_game():
    session = _make_session()
    pawn = Piece(Color.BLACK, PieceType.PAWN)
    session.events.append(Capture(pawn, Color.WHITE))

    with patch("server.game.session.update_ratings") as mock_update:
        session._finalize_ratings()
    mock_update.assert_not_called()


def test_white_captures_black_king_awards_white_the_win():
    session = _make_session()
    session.engine.state.game_over = True
    black_king = Piece(Color.BLACK, PieceType.KING)
    session.events.append(Capture(black_king, Color.WHITE))

    with patch("server.game.session.update_ratings", return_value=(1216, 1184)) as mock_update:
        session._finalize_ratings()

    mock_update.assert_called_once_with("alice", "bob", "white")
    assert session.ratings[Color.WHITE] == 1216
    assert session.ratings[Color.BLACK] == 1184


def test_black_captures_white_king_awards_black_the_win():
    session = _make_session()
    session.engine.state.game_over = True
    white_king = Piece(Color.WHITE, PieceType.KING)
    session.events.append(Capture(white_king, Color.BLACK))

    with patch("server.game.session.update_ratings", return_value=(1184, 1216)) as mock_update:
        session._finalize_ratings()

    mock_update.assert_called_once_with("alice", "bob", "black")


def test_finalize_ratings_is_idempotent():
    session = _make_session()
    session.engine.state.game_over = True
    black_king = Piece(Color.BLACK, PieceType.KING)
    session.events.append(Capture(black_king, Color.WHITE))

    with patch("server.game.session.update_ratings", return_value=(1216, 1184)) as mock_update:
        session._finalize_ratings()
        session._finalize_ratings()

    mock_update.assert_called_once()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.services.elo import apply, expected_score


def test_expected_score_equal_ratings():
    assert expected_score(1200, 1200) == 0.5


def test_expected_score_higher_rating_favored():
    assert expected_score(1400, 1200) > 0.5
    assert expected_score(1200, 1400) < 0.5


def test_apply_equal_ratings_win():
    new_a, new_b = apply(1200, 1200, score_a=1.0, k=32)
    assert (new_a, new_b) == (1216, 1184)


def test_apply_equal_ratings_loss():
    new_a, new_b = apply(1200, 1200, score_a=0.0, k=32)
    assert (new_a, new_b) == (1184, 1216)


def test_apply_draw_no_change_for_equal_ratings():
    new_a, new_b = apply(1200, 1200, score_a=0.5, k=32)
    assert (new_a, new_b) == (1200, 1200)


def test_upset_win_gains_more_than_expected_win():
    # Lower-rated player beating a higher-rated one gains more points...
    upset_gain = apply(1200, 1400, score_a=1.0, k=32)[0] - 1200
    # ...than the higher-rated player gains for beating the lower-rated one.
    expected_gain = apply(1400, 1200, score_a=1.0, k=32)[0] - 1400
    assert upset_gain > expected_gain

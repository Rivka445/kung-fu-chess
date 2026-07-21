"""Standard ELO rating calculation — pure, no DB or I/O."""

K_FACTOR = 32


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def apply(rating_a: int, rating_b: int, score_a: float, k: int = K_FACTOR) -> tuple[int, int]:
    """
    score_a: 1 = a won, 0 = a lost, 0.5 = draw.
    Returns (new_rating_a, new_rating_b), rounded to the nearest int.
    """
    e_a = expected_score(rating_a, rating_b)
    e_b = 1 - e_a
    score_b = 1 - score_a
    new_a = round(rating_a + k * (score_a - e_a))
    new_b = round(rating_b + k * (score_b - e_b))
    return new_a, new_b

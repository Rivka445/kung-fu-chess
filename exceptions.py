"""Custom exception hierarchy for the Kung Fu Chess engine.

All project-specific errors inherit from ChessError, allowing callers to catch
either the base class or a specific subclass as needed.
"""


class ChessError(Exception):
    """Base class for all Kung Fu Chess errors."""


# ── Board parsing errors ──────────────────────────────────────────────────────

class BoardParseError(ChessError):
    """Raised when the board definition cannot be parsed."""


class EmptyRowError(BoardParseError):
    """Raised when a board row contains no tokens."""
    def __init__(self):
        super().__init__("Board row is empty.")


class RowWidthMismatchError(BoardParseError):
    """Raised when a board row has a different number of columns than expected."""
    def __init__(self, expected: int, got: int):
        super().__init__(f"Expected {expected} columns, got {got}.")
        self.expected = expected
        self.got = got


class UnknownTokenError(BoardParseError):
    """Raised when a cell token is not '.' and is not a valid piece string."""
    def __init__(self, token: str):
        super().__init__(f"Unknown board token: '{token}'.")
        self.token = token


# ── Position / notation errors ────────────────────────────────────────────────

class InvalidNotationError(ChessError):
    """Raised when a chess-notation string cannot be parsed (e.g. 'z9')."""
    def __init__(self, notation: str):
        super().__init__(f"Invalid chess notation: '{notation}'.")
        self.notation = notation


class OutOfBoundsError(ChessError):
    """Raised when a position lies outside the board boundaries."""
    def __init__(self, row: int, col: int):
        super().__init__(f"Position ({row}, {col}) is out of bounds.")
        self.row = row
        self.col = col

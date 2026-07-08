from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    """Represents the two possible colors of a chess piece: white or black."""
    WHITE = "w"
    BLACK = "b"


class PieceType(Enum):
    """Represents all possible chess piece types used in the game."""
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "P"


# Piece types that can be blocked by other pieces standing in their path
BLOCKABLE = {PieceType.ROOK, PieceType.BISHOP, PieceType.QUEEN}

# Valid single-character strings for color and piece type, used for input validation
VALID_COLORS = {c.value for c in Color}
VALID_PIECE_TYPES = {p.value for p in PieceType}


@dataclass(frozen=True)
class Piece:
    """Immutable representation of a chess piece, defined by its color and type."""
    color: Color
    type: PieceType

    @staticmethod
    def from_str(s: str) -> "Piece":
        """Creates a Piece from a two-character string such as 'wR' for white rook or 'bK' for black king."""
        return Piece(Color(s[0]), PieceType(s[1]))

    def to_str(self) -> str:
        """Converts the piece back to its two-character string representation, e.g. 'wR' or 'bK'."""
        return self.color.value + self.type.value

    def same_color(self, other: "Piece") -> bool:
        """Returns True if this piece and the other piece share the same color."""
        return self.color == other.color

    @property
    def is_king(self) -> bool:
        """Returns True if this piece is a king."""
        return self.type == PieceType.KING

    @property
    def is_pawn(self) -> bool:
        """Returns True if this piece is a pawn."""
        return self.type == PieceType.PAWN

    @property
    def is_blockable(self) -> bool:
        """Returns True if this piece can be blocked by other pieces along its path (rook, bishop, queen)."""
        return self.type in BLOCKABLE

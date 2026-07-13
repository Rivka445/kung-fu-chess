from dataclasses import dataclass
from enum import Enum


# ---- Enums ----

class Color(Enum):
    """Piece color — white or black."""
    WHITE = "w"
    BLACK = "b"


class PieceType(Enum):
    """Piece type — the six classic chess pieces."""
    KING   = "K"
    QUEEN  = "Q"
    ROOK   = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN   = "P"


# ---- Constants ----

# Pieces whose movement can be blocked by other pieces (unlike king, knight, pawn)
BLOCKABLE = {PieceType.ROOK, PieceType.BISHOP, PieceType.QUEEN}

# Valid string values for each enum — used for input validation during parsing
VALID_COLORS      = {c.value for c in Color}
VALID_PIECE_TYPES = {p.value for p in PieceType}


# ---- Piece ----

@dataclass(frozen=True)
class Piece:
    """
    Immutable representation of a chess piece.
    frozen=True ensures the object cannot be modified after creation,
    and allows it to be used as a dict key or set member.
    """
    color: Color
    type: PieceType

    @staticmethod
    def from_str(s: str) -> "Piece":
        """Create a piece from a 2-character string — first char is color, second is type.
        Example: 'wQ' -> white queen."""
        return Piece(Color(s[0]), PieceType(s[1]))

    def to_str(self) -> str:
        """Convert the piece to a 2-character string.
        Example: white queen -> 'wQ'."""
        return self.color.value + self.type.value

    def same_color(self, other: "Piece") -> bool:
        """Return True if both pieces share the same color."""
        return self.color == other.color

    @property
    def is_king(self) -> bool:
        """Whether this piece is a king."""
        return self.type == PieceType.KING

    @property
    def is_pawn(self) -> bool:
        """Whether this piece is a pawn."""
        return self.type == PieceType.PAWN

    @property
    def is_blockable(self) -> bool:
        """Whether this piece's movement can be blocked (rook, bishop, queen)."""
        return self.type in BLOCKABLE

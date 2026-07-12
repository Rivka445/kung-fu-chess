from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    WHITE = "w"
    BLACK = "b"


class PieceType(Enum):
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "P"


BLOCKABLE = {PieceType.ROOK, PieceType.BISHOP, PieceType.QUEEN}
VALID_COLORS = {c.value for c in Color}
VALID_PIECE_TYPES = {p.value for p in PieceType}


@dataclass(frozen=True)
class Piece:
    color: Color
    type: PieceType

    @staticmethod
    def from_str(s: str) -> "Piece":
        return Piece(Color(s[0]), PieceType(s[1]))

    def to_str(self) -> str:
        return self.color.value + self.type.value

    def same_color(self, other: "Piece") -> bool:
        return self.color == other.color

    @property
    def is_king(self) -> bool:
        return self.type == PieceType.KING

    @property
    def is_pawn(self) -> bool:
        return self.type == PieceType.PAWN

    @property
    def is_blockable(self) -> bool:
        return self.type in BLOCKABLE

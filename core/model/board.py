from core.model.piece import Piece, PieceType, Color
from core.model.position import Position


class Board:
    """
    The physical chess board — a 2D matrix of pieces.
    Responsible for reading/writing pieces, validating positions,
    computing paths, and applying physical moves.
    Does NOT know chess rules — that is the responsibility of RuleEngine.
    """

    def __init__(self) -> None:
        self.matrix: list[list[Piece | None]] = []
        self.expected_cols: int | None = None  # Set by the first row added

    # ---- Board Construction ----

    def add_parsed_row(self, row: list[Piece | None]) -> None:
        """Append a parsed row to the board. The first row determines the expected column count."""
        if self.expected_cols is None:
            self.expected_cols = len(row)
        self.matrix.append(row)

    # ---- Position Queries ----

    def is_inside(self, pos: Position) -> bool:
        """Return True if the position is within the board boundaries."""
        if self.expected_cols is None:
            return False
        return 0 <= pos.row < len(self.matrix) and 0 <= pos.col < self.expected_cols

    def get_piece(self, pos: Position) -> Piece | None:
        """Return the piece at the given position, or None if the square is empty."""
        return self.matrix[pos.row][pos.col]

    def set_piece(self, pos: Position, piece: Piece | None) -> None:
        """Place a piece (or None) at the given position."""
        self.matrix[pos.row][pos.col] = piece

    def same_color(self, p1: Piece | None, p2: Piece | None) -> bool:
        """Return True if both pieces exist and share the same color."""
        return p1 is not None and p2 is not None and p1.same_color(p2)

    # ---- Path & Blocking ----

    def path(self, source: Position, target: Position) -> list[Position]:
        """
        Return all positions between source and target (exclusive of source, inclusive of target).
        Only supports straight lines and diagonals — raises ValueError for non-linear moves.
        Used as the foundation for blocker detection.
        """
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        if dr != 0 and dc != 0 and dr != dc:
            raise ValueError(f"path() called with non-linear move: {source} -> {target}")

        # Determine step direction for each axis (-1, 0, or 1)
        def step(d): return 1 if d > 0 else (-1 if d < 0 else 0)
        rs = step(target.row - source.row)
        cs = step(target.col - source.col)

        result = []
        r, c = source.row + rs, source.col + cs
        while True:
            result.append(Position(r, c))
            if r == target.row and c == target.col:
                break
            r += rs
            c += cs
        return result

    def intermediate_positions(self, source: Position, target: Position) -> list[Position]:
        """Return all positions between source and target, excluding the target itself.
        Used to check for blockers — the target square may legally contain an enemy piece."""
        return self.path(source, target)[:-1]

    def has_blockers(self, source: Position, target: Position) -> bool:
        """Return True if any piece occupies a square between source and target."""
        return any(self.get_piece(pos) is not None for pos in self.intermediate_positions(source, target))

    # ---- Piece Operations ----

    def move_piece(self, source: Position, target: Position) -> None:
        """Move a piece from source to target, clearing the source square."""
        self.set_piece(target, self.get_piece(source))
        self.set_piece(source, None)

    def remove_piece(self, pos: Position) -> None:
        """Remove the piece at the given position (capture or collision)."""
        self.set_piece(pos, None)

    def promote_pawn(self, pos: Position) -> None:
        """Promote a pawn to a queen if it has reached the last row."""
        piece = self.get_piece(pos)
        if piece is None or not piece.is_pawn:
            return
        # White promotes at row 0, black at the last row
        last_row = 0 if piece.color == Color.WHITE else len(self.matrix) - 1
        if pos.row == last_row:
            self.set_piece(pos, Piece(piece.color, PieceType.QUEEN))

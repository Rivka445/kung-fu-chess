from models.piece import Piece, PieceType, Color
from models.position import Position


class ChessBoard:
    def __init__(self):
        self.matrix = []
        self.expected_cols = None

    def add_parsed_row(self, row: list):
        if self.expected_cols is None:
            self.expected_cols = len(row)
        self.matrix.append(row)

    def is_inside(self, pos: Position) -> bool:
        if self.expected_cols is None:
            return False
        return 0 <= pos.row < len(self.matrix) and 0 <= pos.col < self.expected_cols

    def get_piece(self, pos: Position):
        return self.matrix[pos.row][pos.col]

    def set_piece(self, pos: Position, piece):
        self.matrix[pos.row][pos.col] = piece

    def same_color(self, p1, p2) -> bool:
        return p1 is not None and p2 is not None and p1.same_color(p2)

    def has_blockers(self, source: Position, target: Position) -> bool:
        for pos in self.path(source, target)[:-1]:
            if self.get_piece(pos) is not None:
                return True
        return False

    def _step(self, diff):
        return 1 if diff > 0 else (-1 if diff < 0 else 0)

    def path(self, source: Position, target: Position):
        row_step = self._step(target.row - source.row)
        col_step = self._step(target.col - source.col)
        path = []
        r, c = source.row + row_step, source.col + col_step
        while True:
            path.append(Position(r, c))
            if r == target.row and c == target.col:
                break
            r += row_step
            c += col_step
        return path

    def move_piece(self, source: Position, target: Position):
        piece = self.get_piece(source)
        self.set_piece(target, piece)
        self.set_piece(source, None)

    def remove_piece(self, pos: Position):
        self.set_piece(pos, None)

    def promote_pawn(self, pos: Position):
        piece = self.get_piece(pos)
        if piece is None or not piece.is_pawn:
            return
        last_row = 0 if piece.color == Color.WHITE else len(self.matrix) - 1
        if pos.row == last_row:
            self.set_piece(pos, Piece(piece.color, PieceType.QUEEN))

    def print_board(self):
        for row in self.matrix:
            print(" ".join(p.to_str() if p is not None else "." for p in row))

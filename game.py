from dataclasses import dataclass
from position import Position
from piece import PieceType
from rules import is_legal_move, is_legal_pawn_move, BLOCKABLE_PIECES
from config import MOVE_DURATION


@dataclass(frozen=True)
class PendingMove:
    source: Position
    target: Position
    arrival: int


@dataclass(frozen=True)
class AirbornePiece:
    cell: Position
    landing_time: int


class Game:
    def __init__(self, board):
        self.board = board
        self.selected = None
        self.current_time = 0
        self.pending_moves = []
        self.airborne = []
        self.cooldowns = {}
        self.game_over = False

    def handle_click(self, x, y, cell_size):
        if self.game_over:
            return
        pos = Position(y // cell_size, x // cell_size)
        if not self.board.is_inside(pos):
            return
        piece = self.board.get_piece(pos)
        if piece is not None:
            self._handle_piece_click(pos)
        else:
            self._handle_empty_click(pos)

    def _handle_piece_click(self, pos: Position):
        if self.selected is None:
            self.selected = pos
            return
        selected_piece = self.board.get_piece(self.selected)
        clicked_piece = self.board.get_piece(pos)
        if self.board.same_color(selected_piece, clicked_piece):
            self.selected = pos
        else:
            self._request_move(self.selected, pos)
            self.selected = None

    def _handle_empty_click(self, pos: Position):
        if self.selected is None:
            return
        self._request_move(self.selected, pos)
        self.selected = None

    def _request_move(self, source: Position, target: Position):
        piece = self.board.get_piece(source)

        if any(m.source == source for m in self.pending_moves):
            return
        if self.cooldowns.get(source, 0) > self.current_time:
            return
        if self._route_conflicts(source, target):
            return

        if piece.is_pawn:
            target_piece = self.board.get_piece(target)
            board_rows = len(self.board.matrix)
            if is_legal_pawn_move(piece, source, target, target_piece, board_rows):
                if abs(target.row - source.row) == 2 and self.board.has_blockers(source, target):
                    return
                self.pending_moves.append(PendingMove(source, target, self.current_time + MOVE_DURATION))
            return

        if not is_legal_move(piece, source, target):
            return
        if self.board.same_color(piece, self.board.get_piece(target)):
            return
        if piece.is_blockable and self.board.has_blockers(source, target):
            return

        self.pending_moves.append(PendingMove(source, target, self.current_time + MOVE_DURATION))

    def _route_conflicts(self, source: Position, target: Position) -> bool:
        new_cols = set(range(min(source.col, target.col), max(source.col, target.col) + 1))
        return any(
            new_cols & set(range(min(m.source.col, m.target.col), max(m.source.col, m.target.col) + 1))
            for m in self.pending_moves
        )

    def handle_wait(self, ms):
        if self.game_over:
            return
        self.current_time += ms
        ready = [m for m in self.pending_moves if m.arrival <= self.current_time]
        self.pending_moves = [m for m in self.pending_moves if m.arrival > self.current_time]

        landed = [a for a in self.airborne if a.landing_time <= self.current_time]
        self.airborne = [a for a in self.airborne if a.landing_time > self.current_time]
        for a in landed:
            self.cooldowns[a.cell] = a.landing_time + MOVE_DURATION

        simultaneous = {m.target for m in ready if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1}

        for move in sorted(ready, key=lambda m: m.arrival):
            if move.target in simultaneous:
                self.board.remove_piece(move.target)
                continue
            source_piece = self.board.get_piece(move.source)
            target_piece = self.board.get_piece(move.target)
            airborne_here = next((a for a in self.airborne + landed if a.cell == move.target), None)
            if airborne_here is not None and target_piece is not None and not source_piece.same_color(target_piece):
                self.board.remove_piece(move.source)
                continue
            if target_piece is not None and source_piece.same_color(target_piece):
                continue
            self.board.move_piece(move.source, move.target)
            if target_piece is not None and target_piece.is_king:
                self.game_over = True
            self.board.promote_pawn(move.target)
            self.cooldowns[move.target] = move.arrival + MOVE_DURATION

    def handle_jump(self, x, y, cell_size):
        if self.game_over:
            return
        pos = Position(y // cell_size, x // cell_size)
        if not self.board.is_inside(pos):
            return
        if self.board.get_piece(pos) is None:
            return
        if any(m.source == pos for m in self.pending_moves):
            return
        if any(a.cell == pos for a in self.airborne):
            return
        if self.cooldowns.get(pos, 0) > self.current_time:
            return
        self.airborne.append(AirbornePiece(pos, self.current_time + MOVE_DURATION))

    def handle_print_board(self):
        self.board.print_board()

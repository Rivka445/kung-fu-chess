from collections import namedtuple
from pieces import is_legal_move, is_legal_pawn_move, BLOCKABLE_PIECES
from config import MOVE_DURATION

PendingMove = namedtuple("PendingMove", ["source", "target", "arrival"])

class Game:
    def __init__(self, board):
        self.board = board
        self.selected = None
        self.current_time = 0
        self.pending_moves = []
        self.game_over = False

    def handle_click(self, x, y, cell_size):
        if self.game_over:
            return
        row = y // cell_size
        col = x // cell_size

        if not self.board.is_inside(row, col):
            return

        clicked_piece = self.board.get_piece(row, col)

        if clicked_piece != ".":
            self.handle_piece_click(row, col)
        else:
            self.handle_empty_click(row, col)

    def handle_piece_click(self, row, col):
        if self.selected is None:
            self.selected = (row, col)
            return

        selected_row, selected_col = self.selected
        selected_piece = self.board.get_piece(selected_row, selected_col)
        clicked_piece = self.board.get_piece(row, col)

        if self.board.same_color(selected_piece, clicked_piece):
            self.selected = (row, col)
        else:
            self.request_move(self.selected, (row, col))
            self.selected = None

    def handle_empty_click(self, row, col):
        if self.selected is None:
            return

        self.request_move(self.selected, (row, col))
        self.selected = None

    def request_move(self, source, target):
        source_row, source_col = source
        target_row, target_col = target

        piece = self.board.get_piece(source_row, source_col)

        if any(m.source == source for m in self.pending_moves):
            return

        if self.route_conflicts(source_row, source_col, target_row, target_col):
            return

        if piece[1] == "P":
            target_piece = self.board.get_piece(target_row, target_col)
            board_rows = len(self.board.matrix)
            if is_legal_pawn_move(piece, source_row, source_col, target_row, target_col, target_piece, board_rows):
                if abs(target_row - source_row) == 2 and self.board.has_blockers(source_row, source_col, target_row, target_col):
                    return
                self.pending_moves.append(PendingMove(source, target, self.current_time + MOVE_DURATION))
            return
        
        if not is_legal_move(piece, source_row, source_col, target_row, target_col):
            return

        if self.board.target_has_same_color(source_row, source_col, target_row, target_col):
            return

        if piece[1] in BLOCKABLE_PIECES:
            if self.board.has_blockers(source_row, source_col, target_row, target_col):
                return

        self.pending_moves.append(PendingMove(source, target, self.current_time + MOVE_DURATION))

    def route_conflicts(self, source_row, source_col, target_row, target_col):
        new_cols = set(range(min(source_col, target_col), max(source_col, target_col) + 1))
        return any(
            new_cols & set(range(min(m.source[1], m.target[1]), max(m.source[1], m.target[1]) + 1))
            for m in self.pending_moves
        )

    def handle_wait(self, ms):
        if self.game_over:
            return
        self.current_time += ms
        ready = [m for m in self.pending_moves if m.arrival <= self.current_time]
        pending = [m for m in self.pending_moves if m.arrival > self.current_time]

        simultaneous = {m.target for m in ready if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1}

        for move in sorted(ready, key=lambda m: m.arrival):
            if move.target in simultaneous:
                self.board.remove_piece(*move.target)
                continue
            target_piece = self.board.get_piece(*move.target)
            source_piece = self.board.get_piece(*move.source)
            if target_piece != "." and self.board.same_color(source_piece, target_piece):
                continue
            self.board.move_piece(*move.source, *move.target)
            if target_piece in ("wK", "bK"):
                self.game_over = True
            self.board.promote_pawn(*move.target)

        self.pending_moves = pending

    def handle_print_board(self):
        self.board.print_board()


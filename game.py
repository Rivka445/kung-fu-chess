from pieces import is_legal_move, is_legal_pawn_move
from config import MOVE_DURATION

class Game:
    def __init__(self, board):
        self.board = board
        self.selected = None
        self.current_time = 0
        self.pending_moves = []

    def handle_click(self, x, y, cell_size):
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

        if piece[1] == "P":
            target_piece = self.board.get_piece(target_row, target_col)
            if is_legal_pawn_move(piece, source_row, source_col, target_row, target_col, target_piece):
                self.pending_moves.append((source, target, self.current_time + MOVE_DURATION))
            return
        
        if not is_legal_move(piece, source_row, source_col, target_row, target_col):
            return

        if self.board.target_has_same_color(source_row, source_col, target_row, target_col):
            return

        if self.needs_blocker_check(piece):
            if self.board.has_blockers(source_row, source_col, target_row, target_col):
                return

        self.pending_moves.append((source, target, self.current_time + MOVE_DURATION))

    def needs_blocker_check(self, piece):
        return piece[1] in {"R", "B", "Q"}

    def handle_wait(self, ms):
        self.current_time += ms
        ready = [m for m in self.pending_moves if m[2] < self.current_time]
        for source, target, _ in ready:
            self.board.move_piece(*source, *target)
        self.pending_moves = [m for m in self.pending_moves if m[2] >= self.current_time]

    def handle_print_board(self):
        self.board.print_board()


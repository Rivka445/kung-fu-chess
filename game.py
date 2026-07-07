from pieces import is_legal_move
CELL_SIZE = 100

class Game:
    def __init__(self, board):
        self.board = board
        self.selected = None
        self.current_time = 0

    def handle_click(self, x, y):
        row = y // CELL_SIZE
        col = x // CELL_SIZE

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

        if self.same_color(selected_piece, clicked_piece):
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
            if self.is_legal_pawn_move(
                piece,
                source_row,
                source_col,
                target_row,
                target_col
            ):
                self.board.move_piece(source_row, source_col, target_row, target_col)
            return
        
        if not is_legal_move(piece, source_row, source_col, target_row, target_col):
            return

        if self.board.target_has_same_color(source_row, source_col, target_row, target_col):
            return

        if self.needs_blocker_check(piece):
            if self.board.has_blockers(source_row, source_col, target_row, target_col):
                return

        self.board.move_piece(source_row, source_col, target_row, target_col)

    def is_legal_pawn_move(self, piece, source_row, source_col, target_row, target_col):
        color = piece[0]
        target_piece = self.board.get_piece(target_row, target_col)

        row_diff = target_row - source_row
        col_diff = target_col - source_col

        if color == "w":
            expected_row_diff = -1
        else:
            expected_row_diff = 1

        if row_diff != expected_row_diff:
            return False

        if col_diff == 0:
            return target_piece == "."

        if abs(col_diff) == 1:
            return target_piece != "." and target_piece[0] != color

        return False
    
    def needs_blocker_check(self, piece):
        return piece[1] in {"R", "B", "Q"}

    def handle_wait(self, ms):
        self.current_time += ms

    def handle_print_board(self):
        self.board.print_board()

    def same_color(self, piece1, piece2):
        return piece1[0] == piece2[0]
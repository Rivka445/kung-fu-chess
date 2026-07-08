from models.position import Position
from models.game_state import GameState, PendingMove, AirbornePiece
from config import MOVE_DURATION


class Game:
    def __init__(self, board, rules):
        self.board = board
        self.rules = rules
        self.state = GameState()

    def handle_click(self, x, y, cell_size):
        if self.state.game_over:
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
        if self.state.selected is None:
            self.state.selected = pos
            return
        selected_piece = self.board.get_piece(self.state.selected)
        clicked_piece = self.board.get_piece(pos)
        if self.board.same_color(selected_piece, clicked_piece):
            self.state.selected = pos
        else:
            self._request_move(self.state.selected, pos)
            self.state.selected = None

    def _handle_empty_click(self, pos: Position):
        if self.state.selected is None:
            return
        self._request_move(self.state.selected, pos)
        self.state.selected = None

    def _request_move(self, source: Position, target: Position):
        piece = self.board.get_piece(source)

        if self.state.is_busy(source):
            return
        if self._route_conflicts(source, target):
            return

        if piece.is_pawn:
            target_piece = self.board.get_piece(target)
            board_rows = len(self.board.matrix)
            has_blocker = abs(target.row - source.row) == 2 and self.board.has_blockers(source, target)
            if self.rules.is_legal_pawn_move(piece, source, target, target_piece, board_rows, has_blocker):
                self.state.pending_moves.append(PendingMove(source, target, self.state.current_time + MOVE_DURATION))
            return

        if not self.rules.is_legal_move(piece, source, target):
            return
        if self.board.same_color(piece, self.board.get_piece(target)):
            return
        if piece.is_blockable and self.board.has_blockers(source, target):
            return

        self.state.pending_moves.append(PendingMove(source, target, self.state.current_time + MOVE_DURATION))

    def _route_conflicts(self, source: Position, target: Position) -> bool:
        new_path = set(self.board.path(source, target)) | {source}
        return any(
            self.rules.paths_conflict(new_path, set(self.board.path(m.source, m.target)) | {m.source})
            for m in self.state.pending_moves
        )

    def handle_wait(self, ms):
        if self.state.game_over:
            return
        self.state.current_time += ms
        ready, landed = self._advance_time()
        self._process_landings(landed)
        simultaneous = {m.target for m in ready if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1}
        for move in sorted(ready, key=lambda m: m.arrival):
            self._apply_move(move, simultaneous, landed)

    def _advance_time(self):
        ready = [m for m in self.state.pending_moves if m.arrival <= self.state.current_time]
        self.state.pending_moves = [m for m in self.state.pending_moves if m.arrival > self.state.current_time]
        landed = [a for a in self.state.airborne if a.landing_time <= self.state.current_time]
        self.state.airborne = [a for a in self.state.airborne if a.landing_time > self.state.current_time]
        return ready, landed

    def _process_landings(self, landed):
        for a in landed:
            self.state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION

    def _apply_move(self, move, simultaneous, landed):
        if move.target in simultaneous:
            self.board.remove_piece(move.target)
            return
        source_piece = self.board.get_piece(move.source)
        target_piece = self.board.get_piece(move.target)
        airborne_here = next((a for a in self.state.airborne + landed if a.cell == move.target), None)
        if airborne_here is not None and target_piece is not None and not source_piece.same_color(target_piece):
            self.board.remove_piece(move.source)
            return
        if target_piece is not None and source_piece.same_color(target_piece):
            return
        self.board.move_piece(move.source, move.target)
        if target_piece is not None and target_piece.is_king:
            self.state.game_over = True
        self.board.promote_pawn(move.target)
        self.state.cooldowns[move.target] = move.arrival + MOVE_DURATION

    def handle_jump(self, x, y, cell_size):
        if self.state.game_over:
            return
        pos = Position(y // cell_size, x // cell_size)
        if not self.board.is_inside(pos):
            return
        if self.board.get_piece(pos) is None:
            return
        if self.state.is_busy(pos):
            return
        self.state.airborne.append(AirbornePiece(pos, self.state.current_time + MOVE_DURATION))

    def handle_print_board(self):
        self.board.print_board()

from models.position import Position
from models.game_state import GameState, PendingMove, AirbornePiece
from observers.base import GameEventListener
from observers.log_listener import LogListener
from constants import MOVE_DURATION
from logger import logger


class Game:
    """Main game controller for Kung Fu Chess.
    Coordinates between the board, rules, and game state to handle player input and advance the game over time."""

    def __init__(self, board, rules):
        """Initializes the game with a board and a rules engine, and creates a fresh game state."""
        self.board = board
        self.rules = rules
        self.state = GameState()
        self._listeners: list[GameEventListener] = [LogListener()]

    def add_listener(self, listener: GameEventListener):
        """Registers a new subscriber to receive game events."""
        self._listeners.append(listener)

    def _notify_move_applied(self, source, target):
        for l in self._listeners: l.on_move_applied(source, target)

    def _notify_king_captured(self, pos):
        for l in self._listeners: l.on_king_captured(pos)

    def _notify_pawn_promoted(self, pos):
        for l in self._listeners: l.on_pawn_promoted(pos)

    def _notify_collision(self, pos):
        for l in self._listeners: l.on_collision(pos)

    def handle_click(self, x, y, cell_size):
        """Handles a click at pixel coordinates (x, y).
        Converts the click to a board position and either selects a piece or attempts to move the previously selected piece."""
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
        """Handles a click on a cell that contains a piece.
        If no piece is selected yet, selects this one. If a piece is already selected and the clicked piece is the same color, switches selection.
        If the clicked piece is an enemy, attempts to move the selected piece to capture it."""
        if self.state.selected is None:
            logger.debug("selected %s at %s", self.board.get_piece(pos).to_str(), pos)
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
        """Handles a click on an empty cell.
        If a piece is currently selected, attempts to move it to this position."""
        if self.state.selected is None:
            return
        self._request_move(self.state.selected, pos)
        self.state.selected = None

    def _request_move(self, source: Position, target: Position):
        """Validates and registers a move from source to target.
        Checks that the piece is not busy, the move shape is legal, the target is not occupied by a friendly piece,
        and for blockable pieces that the path is clear. If all checks pass, adds a PendingMove to the game state."""
        piece = self.board.get_piece(source)

        if self.state.is_busy(source):
            logger.debug("move rejected — %s at %s is busy", piece.to_str(), source)
            return

        if piece.is_pawn:
            target_piece = self.board.get_piece(target)
            board_rows = len(self.board.matrix)
            has_blocker = abs(target.row - source.row) == 2 and self.board.has_blockers(source, target)
            if self.rules.is_legal_pawn_move(piece, source, target, target_piece, board_rows, has_blocker):
                self.state.pending_moves.append(PendingMove(source, target, self.state.current_time + MOVE_DURATION))
                logger.info("queued pawn move %s → %s", source, target)
            else:
                logger.debug("illegal pawn move %s → %s", source, target)
            return

        if not self.rules.is_legal_move(piece, source, target):
            logger.debug("illegal move shape %s: %s → %s", piece.to_str(), source, target)
            return
        if self.board.same_color(piece, self.board.get_piece(target)):
            logger.debug("move rejected — friendly piece at %s", target)
            return
        if piece.is_blockable and self.board.has_blockers(source, target):
            logger.debug("move rejected — path blocked %s → %s", source, target)
            return

        self.state.pending_moves.append(PendingMove(source, target, self.state.current_time + MOVE_DURATION))
        logger.info("queued move %s: %s → %s", piece.to_str(), source, target)

    def handle_wait(self, ms):
        """Advances the game clock by the given number of milliseconds.
        Processes all moves and airborne pieces that have reached their destination during this time window."""
        if self.state.game_over:
            return
        self.state.current_time += ms
        ready, landed = self._advance_time()
        self._process_landings(landed)
        simultaneous = {m.target for m in ready if sum(1 for o in ready if o.target == m.target and o.arrival == m.arrival) > 1}
        for move in sorted(ready, key=lambda m: m.arrival):
            self._apply_move(move, simultaneous, landed)

    def _advance_time(self):
        """Separates pending moves and airborne pieces into those that have arrived and those still in transit.
        Returns two lists: moves that are ready to be applied, and pieces that have just landed."""
        ready = [m for m in self.state.pending_moves if m.arrival <= self.state.current_time]
        self.state.pending_moves = [m for m in self.state.pending_moves if m.arrival > self.state.current_time]
        landed = [a for a in self.state.airborne if a.landing_time <= self.state.current_time]
        self.state.airborne = [a for a in self.state.airborne if a.landing_time > self.state.current_time]
        return ready, landed

    def _process_landings(self, landed):
        """Registers a cooldown for each piece that has just landed.
        The cooldown prevents the piece from being moved again immediately after landing."""
        for a in landed:
            self.state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION

    def _apply_move(self, move, simultaneous, landed):
        """Applies a single move that has reached its destination.
        Handles simultaneous collisions, airborne interactions, friendly piece blocking, captures, king capture, and pawn promotion."""
        if move.target in simultaneous:
            self.board.remove_piece(move.target)
            self._notify_collision(move.target)
            return
        source_piece = self.board.get_piece(move.source)
        target_piece = self.board.get_piece(move.target)
        airborne_here = next((a for a in self.state.airborne + landed if a.cell == move.target), None)
        if airborne_here is not None and target_piece is not None and not source_piece.same_color(target_piece):
            self.board.remove_piece(move.source)
            self._notify_collision(move.target)
            return
        if target_piece is not None and source_piece.same_color(target_piece):
            return
        self.board.move_piece(move.source, move.target)
        self._notify_move_applied(move.source, move.target)
        if target_piece is not None and target_piece.is_king:
            self.state.game_over = True
            self._notify_king_captured(move.target)
        if self.board.get_piece(move.target) and self.board.get_piece(move.target).is_pawn:
            self.board.promote_pawn(move.target)
            self._notify_pawn_promoted(move.target)
        else:
            self.board.promote_pawn(move.target)
        self.state.cooldowns[move.target] = move.arrival + MOVE_DURATION

    def handle_jump(self, x, y, cell_size):
        """Handles a jump command at pixel coordinates (x, y).
        If the cell contains a piece that is not busy, launches it into the air as an AirbornePiece."""
        if self.state.game_over:
            return
        pos = Position(y // cell_size, x // cell_size)
        if not self.board.is_inside(pos):
            return
        if self.board.get_piece(pos) is None:
            return
        if self.state.is_busy(pos):
            return
        logger.info("jump: %s launched from %s", self.board.get_piece(pos).to_str(), pos)
        self.state.airborne.append(AirbornePiece(pos, self.state.current_time + MOVE_DURATION))

    def handle_print_board(self):
        """Delegates to the board to print its current state to stdout."""
        self.board.print_board()

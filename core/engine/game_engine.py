from core.model.board import Board
from core.model.game_state import GameState, PendingMove
from core.model.position import Position
from core.rules.rule_engine import RuleEngine
from core.real_time.real_time_arbiter import RealTimeArbiter
from core.events.event_bus import EventBus, GameStarted, GameOver
from constants import MOVE_DURATION
from logger import logger


class GameEngine:
    """
    Central facade for the chess game.
    Connects all subsystems: board, rules, real-time arbitration, and event listeners.
    External code (controller, tests) interacts only with this class.
    """

    def __init__(self, board: Board, rules: RuleEngine):
        self.board = board
        self.rules = rules
        self.state = GameState()
        self.bus = EventBus()
        self._arbiter = RealTimeArbiter(board, self.bus)
        self.bus.publish(GameStarted())

    def request_move(self, source: Position, target: Position):
        """
        Submit a move request from source to target.
        The move is queued as a PendingMove if all checks pass:
          1. The game is still ongoing.
          2. The piece at source is idle (not in-flight or on cooldown).
          3. The move is legal according to chess rules.
        Arrival time is calculated based on the distance of the move.
        """
        if self.state.game_over:
            return

        piece = self.board.get_piece(source)

        if piece is None:
            return

        # Reject if the piece is busy (in-flight or on cooldown)
        if not self.state.get_status(source).can_act():
            logger.debug("move rejected — %s at %s is %s", piece.to_str(), source, self.state.get_status(source).name())
            return

        # Reject if the move violates chess rules
        if not self.rules.is_legal(piece, source, target, self.board):
            logger.debug("illegal move %s: %s → %s", piece.to_str(), source, target)
            return

        # Calculate arrival time based on Chebyshev distance (max of row/col delta)
        dr = abs(target.row - source.row)
        dc = abs(target.col - source.col)
        distance = max(dr, dc)
        arrival = self.state.current_time + MOVE_DURATION * distance

        self.state.pending_moves.append(PendingMove(source, target, arrival, self.state.next_seq()))
        logger.info("queued move %s: %s → %s", piece.to_str(), source, target)

    def request_jump(self, pos: Position):
        """
        Launch the piece at the given position into the air.
        Ignored if the game is over, the position is invalid, or the piece is busy.
        """
        if self.state.game_over:
            return
        if not self.board.is_inside(pos) or self.board.get_piece(pos) is None:
            return
        if not self.state.get_status(pos).can_act():
            return
        self._arbiter.launch(pos, self.state)

    def advance_time(self, ms: int):
        """
        Advance the game clock by ms milliseconds.
        Triggers the arbiter to process all moves and events due within this time window.
        Ignored if the game is already over.
        """
        if self.state.game_over:
            return
        self._arbiter.advance(ms, self.state)
        if self.state.game_over:
            self.bus.publish(GameOver())

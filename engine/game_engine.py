from model.board import Board
from model.game_state import GameState, PendingMove
from model.position import Position
from rules.rule_engine import RuleEngine
from real_time.real_time_arbiter import RealTimeArbiter
from events.base import GameEventListener
from constants import MOVE_DURATION
from logger import logger


class GameEngine:
    def __init__(self, board: Board, rules: RuleEngine):
        self.board = board
        self.rules = rules
        self.state = GameState()
        self._listeners: list[GameEventListener] = []
        self._arbiter = RealTimeArbiter(board, self._listeners)

    def add_listener(self, listener: GameEventListener):
        self._listeners.append(listener)

    def request_move(self, source: Position, target: Position):
        if self.state.game_over:
            return
        piece = self.board.get_piece(source)
        if self.state.is_busy(source):
            logger.debug("move rejected — %s at %s is busy", piece.to_str(), source)
            return
        if not self.rules.is_legal(piece, source, target, self.board):
            logger.debug("illegal move %s: %s → %s", piece.to_str(), source, target)
            return
        self.state.pending_moves.append(PendingMove(source, target, self.state.current_time + MOVE_DURATION))
        logger.info("queued move %s: %s → %s", piece.to_str(), source, target)

    def request_jump(self, pos: Position):
        if self.state.game_over:
            return
        if not self.board.is_inside(pos) or self.board.get_piece(pos) is None:
            return
        if self.state.is_busy(pos):
            return
        self._arbiter.launch(pos, self.state)

    def advance_time(self, ms: int):
        if self.state.game_over:
            return
        self._arbiter.advance(ms, self.state)

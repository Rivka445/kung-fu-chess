from model.game_state import GameState, AirbornePiece
from model.position import Position
from constants import MOVE_DURATION
from real_time.time_partitioner import TimePartitioner
from real_time.collision_resolver import CollisionResolver
from real_time.move_applier import MoveApplier
from logger import logger


class RealTimeArbiter:
    def __init__(self, board, listeners):
        self._board = board
        self._partitioner = TimePartitioner()
        self._collision = CollisionResolver()
        self._applier = MoveApplier(board, listeners)

    def advance(self, ms: int, state: GameState):
        state.current_time += ms
        ready, landed = self._partitioner.partition(state)
        for a in landed:
            state.cooldowns[a.cell] = a.landing_time + MOVE_DURATION
        ready = self._collision.resolve_head_on(ready)
        simultaneous = self._collision.find_simultaneous(ready)
        for move in sorted(ready, key=lambda m: m.arrival):
            self._applier.apply(move, simultaneous, landed, state)

    def launch(self, pos: Position, state: GameState):
        state.airborne.append(AirbornePiece(pos, state.current_time + MOVE_DURATION))
        logger.info("jump: %s launched from %s", self._board.get_piece(pos).to_str(), pos)

from shared.events.event_bus import EventBus, MoveApplied, Capture, Collision
from shared.model.position import Position
from shared.model.piece import Color
from shared.model.board import Board
from shared.constants.constants import PIECE_POINTS

COL_NAMES = "abcdefgh"


def _sq(pos: Position) -> str:
    """Convert Position to chess notation, e.g. Position(6,4) -> 'e2'."""
    return COL_NAMES[pos.col] + str(8 - pos.row)


def _fmt_time(ms: int) -> str:
    """Format milliseconds as MM:SS.mmm, e.g. 4105 -> '00:04.105'."""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis  = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


class MoveLogger:
    """
    Tracks moves and score per color.
    - moves: dict Color -> list of (time_str, move_str)
    - score: dict Color -> int
    - player_names: dict Color -> str
    """

    def __init__(self, board: Board, bus: EventBus,
                 white_name: str = "White", black_name: str = "Black"):
        self._board = board
        self.player_names = {Color.WHITE: white_name, Color.BLACK: black_name}
        self.moves: dict[Color, list[tuple[str, str]]] = {Color.WHITE: [], Color.BLACK: []}
        self.score:  dict[Color, int]                  = {Color.WHITE: 0,  Color.BLACK: 0}
        self._current_time = 0
        bus.subscribe(MoveApplied, self._on_move_applied)
        bus.subscribe(Capture,     self._on_capture)
        bus.subscribe(Collision,   self._on_collision)

    def tick(self, current_time: int):
        self._current_time = current_time

    def _on_capture(self, event: Capture):
        self.score[event.capturing_color] += PIECE_POINTS.get(event.captured_piece.type.value, 0)

    def _on_move_applied(self, event: MoveApplied):
        piece = self._board.get_piece(event.target)
        if piece is None:
            return
        time_str = _fmt_time(self._current_time)
        move_str = _sq(event.target)
        self.moves[piece.color].append((time_str, move_str))

    def _on_collision(self, event: Collision):
        pass

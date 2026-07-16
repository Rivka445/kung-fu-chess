from events.base import GameEventListener
from model.position import Position
from model.piece import Color
from model.board import Board
from constants import PIECE_POINTS

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


class MoveLogger(GameEventListener):
    """
    Tracks moves and score per color.
    - moves: dict Color -> list of (time_str, move_str)
    - score: dict Color -> int
    - player_names: dict Color -> str
    """

    def __init__(self, board: Board,
                 white_name: str = "White", black_name: str = "Black"):
        self._board = board                        # needed to know which color moved
        self.player_names = {Color.WHITE: white_name, Color.BLACK: black_name}
        self.moves: dict[Color, list[tuple[str, str]]] = {Color.WHITE: [], Color.BLACK: []}
        self.score:  dict[Color, int]               = {Color.WHITE: 0,  Color.BLACK: 0}
        self._current_time = 0                     # updated via on_time so we can timestamp

    def tick(self, current_time: int):
        """Called each frame with the current game clock (ms)."""
        self._current_time = current_time

    def on_capture(self, captured_piece, capturing_color):
        """Add captured piece's value to the capturing side's score."""
        self.score[capturing_color] += PIECE_POINTS.get(captured_piece.type.value, 0)

    def on_move_applied(self, source: Position, target: Position):
        """Record the move under the correct color with a timestamp."""
        piece = self._board.get_piece(target)      # piece already moved to target
        if piece is None:
            return
        time_str = _fmt_time(self._current_time)
        move_str = _sq(target)                     # destination square as move label
        self.moves[piece.color].append((time_str, move_str))

    def on_collision(self, pos: Position):
        pass  # collisions don't count as moves

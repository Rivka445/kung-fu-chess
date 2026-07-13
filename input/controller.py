from engine.game_engine import GameEngine
from input.board_mapper import pixel_to_pos
from model.position import Position


class Controller:
    """
    Handles player input and translates it into game engine actions.
    Manages click-based piece selection and move submission.
    """

    def __init__(self, engine: GameEngine):
        self._engine = engine
        self._selected: Position | None = None  # Currently selected square (first click)

    def click(self, x: int, y: int, cell_size: int):
        """
        Handle a click at pixel coordinates (x, y).
        First click: selects a piece.
        Second click: submits a move from the selected square to the clicked square.
        If the second click lands on a friendly piece, it re-selects instead.
        """
        state = self._engine.state
        board = self._engine.board

        if state.game_over:
            return

        pos = pixel_to_pos(x, y, cell_size)
        if not board.is_inside(pos):
            return

        piece = board.get_piece(pos)

        # First click — select a square that has a piece
        if self._selected is None:
            if piece is not None:
                self._selected = pos
            return

        selected_piece = board.get_piece(self._selected)

        # Second click on a friendly piece — re-select
        if piece is not None and board.same_color(selected_piece, piece):
            self._selected = pos
        else:
            # Second click on an empty square or enemy — submit the move
            self._engine.request_move(self._selected, pos)
            self._selected = None

    def jump(self, x: int, y: int, cell_size: int):
        """Launch the piece at pixel coordinates (x, y) into the air."""
        pos = pixel_to_pos(x, y, cell_size)
        self._engine.request_jump(pos)

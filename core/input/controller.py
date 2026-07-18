from core.engine.game_engine import GameEngine
from core.input.board_mapper import pixel_to_pos
from core.model.position import Position


class Controller:
    """
    Handles player input and translates it into game engine actions.
    Manages click-based piece selection and move submission.
    """

    def __init__(self, engine: GameEngine):
        self._engine = engine
        self._selected: Position | None = None  # Currently selected square (first click)

    def click(self, x: int, y: int, cell_size: int,
              offset_x: int = 0, offset_y: int = 0):
        """Handle a click at pixel coordinates — converts to Position and delegates."""
        self.click_pos(pixel_to_pos(x, y, cell_size, offset_x, offset_y))

    def click_pos(self, pos: Position):
        """
        Handle a click at a board position.
        First click: selects a piece.
        Second click: submits a move from the selected square to the clicked square.
        If the second click lands on a friendly piece, it re-selects instead.
        """
        state = self._engine.state
        board = self._engine.board

        if state.game_over:
            return
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

    def jump(self, x: int, y: int, cell_size: int,
             offset_x: int = 0, offset_y: int = 0):
        """Handle a jump at pixel coordinates — converts to Position and delegates."""
        self._engine.request_jump(pixel_to_pos(x, y, cell_size, offset_x, offset_y))

    def jump_pos(self, pos: Position):
        """Launch the piece at the given board position into the air."""
        self._engine.request_jump(pos)

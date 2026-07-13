from engine.game_engine import GameEngine
from input.board_mapper import pixel_to_pos
from model.position import Position


class Controller:
    def __init__(self, engine: GameEngine):
        self._engine = engine
        self._selected: Position | None = None

    def click(self, x: int, y: int, cell_size: int):
        state = self._engine.state
        board = self._engine.board
        if state.game_over:
            return
        pos = pixel_to_pos(x, y, cell_size)
        if not board.is_inside(pos):
            return
        piece = board.get_piece(pos)
        if self._selected is None:
            if piece is not None:
                self._selected = pos
            return
        selected_piece = board.get_piece(self._selected)
        if piece is not None and board.same_color(selected_piece, piece):
            self._selected = pos
        else:
            self._engine.request_move(self._selected, pos)
            self._selected = None

    def jump(self, x: int, y: int, cell_size: int):
        pos = pixel_to_pos(x, y, cell_size)
        self._engine.request_jump(pos)

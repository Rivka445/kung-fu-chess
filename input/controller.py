from engine.game_engine import GameEngine
from input.board_mapper import pixel_to_pos


class Controller:
    def __init__(self, engine: GameEngine):
        self._engine = engine

    def click(self, x: int, y: int, cell_size: int):
        state = self._engine.state
        board = self._engine.board
        if state.game_over:
            return
        pos = pixel_to_pos(x, y, cell_size)
        if not board.is_inside(pos):
            return
        piece = board.get_piece(pos)
        if state.selected is None:
            if piece is not None:
                state.selected = pos
            return
        selected_piece = board.get_piece(state.selected)
        if piece is not None and board.same_color(selected_piece, piece):
            state.selected = pos
        else:
            self._engine.request_move(state.selected, pos)
            state.selected = None

    def jump(self, x: int, y: int, cell_size: int):
        pos = pixel_to_pos(x, y, cell_size)
        self._engine.request_jump(pos)

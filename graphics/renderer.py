import pathlib
import numpy as np
import cv2
from dataclasses import dataclass
from graphics.img import Img
from graphics.sprite import get_sprite_sheet, piece_state
from model.board import Board
from model.game_state import GameState
from model.position import Position
from model.piece import Color
from constants import MOVE_DURATION, MIN_CELL_SIZE, MAX_CELL_SIZE, BOARD_IMAGE

SIDEBAR_W  = 260
COORD_SIZE = 30

COL_LETTERS = "abcdefgh"
FONT        = cv2.FONT_HERSHEY_SIMPLEX
DARK_BG     = (25, 25, 35, 255)
PANEL_BG    = (35, 35, 50, 255)
GOLD        = (0, 200, 255, 255)
WHITE_TXT   = (230, 230, 230, 255)
GRAY_TXT    = (160, 160, 160, 255)
DIVIDER     = (70, 70, 90, 255)



@dataclass(frozen=True)
class Layout:
    """All geometry derived from the current cell size."""
    cell_size:  int
    board_size: int
    canvas_w:   int
    canvas_h:   int
    board_x:    int
    board_y:    int


def make_layout(cell_size: int) -> Layout:
    cell_size  = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, cell_size))
    board_size = cell_size * 8
    board_x    = SIDEBAR_W + COORD_SIZE
    board_y    = COORD_SIZE
    canvas_w   = SIDEBAR_W + COORD_SIZE + board_size + COORD_SIZE + SIDEBAR_W
    canvas_h   = COORD_SIZE + board_size + COORD_SIZE
    return Layout(cell_size, board_size, canvas_w, canvas_h, board_x, board_y)


def _pos_to_px(pos: Position, layout: Layout) -> tuple[int, int]:
    """Top-left pixel of a board cell (relative to full canvas)."""
    return layout.board_x + pos.col * layout.cell_size, layout.board_y + pos.row * layout.cell_size


def _interpolated_px(move, current_time: int, layout: Layout) -> tuple[int, int]:
    """Pixel position of a piece mid-move using linear interpolation."""
    distance   = max(abs(move.target.row - move.source.row),
                     abs(move.target.col - move.source.col))
    start_time = move.arrival - distance * 1000
    t  = (current_time - start_time) / (move.arrival - start_time)
    t  = max(0.0, min(1.0, t))
    sx, sy = _pos_to_px(move.source, layout)
    tx, ty = _pos_to_px(move.target, layout)
    return int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)


def _state_start(pos, state_name: str, game_state: GameState) -> int:
    """Return the time when the piece at pos entered its current state."""
    if state_name in ("short_rest", "long_rest"):
        return game_state.cooldowns.get(pos, 0) - MOVE_DURATION
    if state_name == "move":
        move = next((m for m in game_state.pending_moves if m.source == pos), None)
        if move:
            distance = max(abs(move.target.row - move.source.row),
                           abs(move.target.col - move.source.col))
            return move.arrival - MOVE_DURATION * distance
    return game_state.cooldowns.get(pos, 0)


def _txt(bg, text, x, y, scale=0.5, color=WHITE_TXT, bold=False):
    cv2.putText(bg, text, (x, y), FONT, scale, color, 2 if bold else 1, cv2.LINE_AA)


class _NullMoveLogger:
    """Null Object — used when no logger is provided, returns safe defaults."""
    def __init__(self):
        self.player_names = {Color.WHITE: "White", Color.BLACK: "Black"}
        self.moves        = {Color.WHITE: [],      Color.BLACK: []}
        self.score        = {Color.WHITE: 0,        Color.BLACK: 0}


class Renderer:
    def __init__(self, move_logger=None):
        self._logger    = move_logger or _NullMoveLogger()
        self._board_img = Img().read(str(BOARD_IMAGE))   # loaded once, resized per layout
        self._last_cell_size = None
        self._board_bg  = None

    def _get_board_bg(self, layout: Layout) -> Img:
        """Return board background, resizing only when cell_size changes."""
        if layout.cell_size != self._last_cell_size:
            self._board_bg       = Img().read(str(BOARD_IMAGE), size=(layout.board_size, layout.board_size))
            self._last_cell_size = layout.cell_size
        return self._board_bg

    # ------------------------------------------------------------------ #
    #  Side panel                                                          #
    # ------------------------------------------------------------------ #

    def _draw_table_headers(self, bg, x0: int, header_y: int):
        cv2.line(bg, (x0 + 5, header_y - 5), (x0 + SIDEBAR_W - 5, header_y - 5), DIVIDER, 1)
        _txt(bg, "Time", x0 + 10,  header_y, scale=0.45, color=GRAY_TXT)
        _txt(bg, "Move", x0 + 155, header_y, scale=0.45, color=GRAY_TXT)
        cv2.line(bg, (x0 + 5, header_y + 8), (x0 + SIDEBAR_W - 5, header_y + 8), DIVIDER, 1)

    def _draw_table_rows(self, bg, x0: int, moves: list, header_y: int, layout: Layout):
        max_rows = (layout.board_size - 120) // 26
        for i, (t, m) in enumerate(moves[-max_rows:]):
            y = header_y + 25 + i * 26
            if y > layout.board_y + layout.board_size - 20:
                break
            bg[y - 16:y + 8, x0 + 5:x0 + SIDEBAR_W - 5] = (50, 50, 70, 255) if i % 2 == 0 else PANEL_BG
            _txt(bg, t, x0 + 10,  y, scale=0.42, color=WHITE_TXT)
            _txt(bg, m, x0 + 155, y, scale=0.45, color=GOLD)

    def _draw_panel(self, bg, x0: int, color: Color, layout: Layout):
        bg[:, x0:x0 + SIDEBAR_W] = PANEL_BG
        name  = self._logger.player_names[color]
        moves = self._logger.moves[color]
        score = self._logger.score[color]
        _txt(bg, name,             x0 + 10, 40, scale=0.7,  color=GOLD,              bold=True)
        _txt(bg, f"Score: {score}", x0 + 10, 68, scale=0.55, color=(0, 255, 100, 255), bold=True)
        self._draw_table_headers(bg, x0, header_y=100)
        self._draw_table_rows(bg, x0, moves, header_y=100, layout=layout)

    # ------------------------------------------------------------------ #
    #  Board coordinates                                                   #
    # ------------------------------------------------------------------ #

    def _draw_coordinates(self, bg, layout: Layout):
        for i in range(8):
            cx = layout.board_x + i * layout.cell_size + layout.cell_size // 2 - 7
            _txt(bg, COL_LETTERS[i], cx, layout.board_y + layout.board_size + COORD_SIZE - 5,
                 scale=0.5, color=GRAY_TXT)
            ry = layout.board_y + i * layout.cell_size + layout.cell_size // 2 + 6
            _txt(bg, str(8 - i), layout.board_x - COORD_SIZE + 5, ry, scale=0.5, color=GRAY_TXT)

    # ------------------------------------------------------------------ #
    #  Pieces                                                              #
    # ------------------------------------------------------------------ #

    def _draw_pieces(self, canvas: Img, board: Board, state: GameState, layout: Layout):
        self._draw_stationary(canvas, board, state, layout)
        self._draw_moving(canvas, board, state, layout)
        self._draw_airborne(canvas, board, state, layout)

    def _draw_stationary(self, canvas: Img, board: Board, state: GameState, layout: Layout):
        moving_sources = {m.source for m in state.pending_moves}
        for row in range(len(board.matrix)):
            for col in range(len(board.matrix[row])):
                pos   = Position(row, col)
                piece = board.get_piece(pos)
                if piece is None or pos in moving_sources:
                    continue
                self._draw_stationary_piece(canvas, pos, piece, state, layout)

    def _draw_stationary_piece(self, canvas: Img, pos: Position, piece, state: GameState, layout: Layout):
        sheet = get_sprite_sheet(piece)
        s     = piece_state(pos, state)
        start = _state_start(pos, s, state)
        frame = sheet.get_frame(s, state.current_time, start)
        x, y  = _pos_to_px(pos, layout)
        if piece.color == Color.BLACK:
            frame.draw_on_with_outline(canvas, x, y)
        else:
            frame.draw_on(canvas, x, y)

    def _draw_moving(self, canvas: Img, board: Board, state: GameState, layout: Layout):
        for move in state.pending_moves:
            piece = board.get_piece(move.source)
            if piece is None:
                continue
            sheet    = get_sprite_sheet(piece)
            distance = max(abs(move.target.row - move.source.row),
                           abs(move.target.col - move.source.col))
            start    = move.arrival - MOVE_DURATION * distance
            frame    = sheet.get_frame("move", state.current_time, start)
            x, y     = _interpolated_px(move, state.current_time, layout)
            if piece.color == Color.BLACK:
                frame.draw_on_with_outline(canvas, x, y)
            else:
                frame.draw_on(canvas, x, y)

    def _draw_airborne(self, canvas: Img, board: Board, state: GameState, layout: Layout):
        for airborne in state.airborne:
            piece = board.get_piece(airborne.cell)
            if piece is None:
                continue
            sheet = get_sprite_sheet(piece)
            start = airborne.landing_time - MOVE_DURATION
            frame = sheet.get_frame("jump", state.current_time, start)
            x, y  = _pos_to_px(airborne.cell, layout)
            if piece.color == Color.BLACK:
                frame.draw_on_with_outline(canvas, x, y)
            else:
                frame.draw_on(canvas, x, y)

    def _draw_selection(self, bg, selected: Position | None, layout: Layout):
        if selected is None:
            return
        x, y = _pos_to_px(selected, layout)
        overlay = bg.copy()
        cv2.rectangle(overlay, (x, y), (x + layout.cell_size, y + layout.cell_size), (0, 255, 255, 180), -1)
        cv2.addWeighted(overlay, 0.35, bg, 0.65, 0, bg)

    def _draw_game_over(self, canvas: Img, state: GameState, layout: Layout):
        if state.game_over:
            canvas.put_text("GAME OVER", layout.board_x + layout.board_size // 4,
                            layout.board_y + layout.board_size // 2,
                            layout.cell_size / 40, (0, 0, 255, 255), 4)

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def draw(self, board: Board, state: GameState,
             selected: Position | None, cell_size: int) -> Img:
        layout     = make_layout(cell_size)
        canvas     = Img()
        canvas.img = np.full((layout.canvas_h, layout.canvas_w, 4), DARK_BG, dtype=np.uint8)
        bg         = canvas.img

        board_bg = self._get_board_bg(layout)
        bg[layout.board_y:layout.board_y + layout.board_size,
           layout.board_x:layout.board_x + layout.board_size] = board_bg.img

        self._draw_coordinates(bg, layout)
        self._draw_panel(bg, 0, Color.BLACK, layout)
        self._draw_panel(bg, SIDEBAR_W + COORD_SIZE + layout.board_size + COORD_SIZE, Color.WHITE, layout)
        self._draw_selection(bg, selected, layout)
        self._draw_pieces(canvas, board, state, layout)
        self._draw_game_over(canvas, state, layout)
        return canvas, layout

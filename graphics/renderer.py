import pathlib
import numpy as np
import cv2
from graphics.img import Img
from graphics.sprite import get_sprite_sheet, piece_state
from model.board import Board
from model.game_state import GameState
from model.position import Position
from model.piece import Color
from constants import CELL_SIZE, MOVE_DURATION

BOARD_IMG  = pathlib.Path(__file__).parent.parent / "assets" / "assets" / "images" / "board.png"
BOARD_SIZE = CELL_SIZE * 8   # 800
SIDEBAR_W  = 260             # width of each side panel
COORD_SIZE = 30              # pixels for coordinate labels around the board
CANVAS_W   = SIDEBAR_W + COORD_SIZE + BOARD_SIZE + COORD_SIZE + SIDEBAR_W
CANVAS_H   = COORD_SIZE + BOARD_SIZE + COORD_SIZE
BOARD_X    = SIDEBAR_W + COORD_SIZE   # x offset where the board starts
BOARD_Y    = COORD_SIZE               # y offset where the board starts

COL_LETTERS = "abcdefgh"
FONT        = cv2.FONT_HERSHEY_SIMPLEX
DARK_BG     = (25, 25, 35, 255)
PANEL_BG    = (35, 35, 50, 255)
GOLD        = (0, 200, 255, 255)   # BGR: gold-ish
WHITE_TXT   = (230, 230, 230, 255)
GRAY_TXT    = (160, 160, 160, 255)
DIVIDER     = (70, 70, 90, 255)


def _pos_to_px(pos: Position) -> tuple[int, int]:
    """Top-left pixel of a board cell (relative to full canvas)."""
    return BOARD_X + pos.col * CELL_SIZE, BOARD_Y + pos.row * CELL_SIZE


def _interpolated_px(move, current_time: int) -> tuple[int, int]:
    """Pixel position of a piece mid-move using linear interpolation."""
    start_time = move.arrival - (
        max(abs(move.target.row - move.source.row),
            abs(move.target.col - move.source.col)) * 1000
    )
    t = (current_time - start_time) / (move.arrival - start_time)
    t = max(0.0, min(1.0, t))
    sx, sy = _pos_to_px(move.source)
    tx, ty = _pos_to_px(move.target)
    return int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)


def _state_start(pos, state_name: str, game_state: GameState) -> int:
    """Return the time when the piece at pos entered its current state."""
    if state_name in ("short_rest", "long_rest"):
        cooldown_until = game_state.cooldowns.get(pos, 0)
        return cooldown_until - MOVE_DURATION
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
        self._board_bg = Img().read(str(BOARD_IMG), size=(BOARD_SIZE, BOARD_SIZE))
        self._logger   = move_logger or _NullMoveLogger()

    # ------------------------------------------------------------------ #
    #  Side panel                                                          #
    # ------------------------------------------------------------------ #

    def _draw_table_headers(self, bg, x0: int, header_y: int):
        """Draw the Time/Move column headers with divider lines."""
        w = SIDEBAR_W
        cv2.line(bg, (x0 + 5, header_y - 5), (x0 + w - 5, header_y - 5), DIVIDER, 1)
        _txt(bg, "Time", x0 + 10,  header_y, scale=0.45, color=GRAY_TXT)
        _txt(bg, "Move", x0 + 155, header_y, scale=0.45, color=GRAY_TXT)
        cv2.line(bg, (x0 + 5, header_y + 8), (x0 + w - 5, header_y + 8), DIVIDER, 1)

    def _draw_table_rows(self, bg, x0: int, moves: list, header_y: int):
        """Draw alternating move rows below the headers."""
        max_rows = (BOARD_SIZE - 120) // 26
        for i, (t, m) in enumerate(moves[-max_rows:]):
            y = header_y + 25 + i * 26
            if y > BOARD_Y + BOARD_SIZE - 20:
                break
            bg[y - 16:y + 8, x0 + 5:x0 + SIDEBAR_W - 5] = (50, 50, 70, 255) if i % 2 == 0 else PANEL_BG
            _txt(bg, t, x0 + 10,  y, scale=0.42, color=WHITE_TXT)
            _txt(bg, m, x0 + 155, y, scale=0.45, color=GOLD)

    def _draw_move_table(self, bg, x0: int, moves: list, header_y: int):
        """Draw the full move table: headers + rows."""
        self._draw_table_headers(bg, x0, header_y)
        self._draw_table_rows(bg, x0, moves, header_y)

    def _draw_panel(self, bg, x0: int, color: Color):
        """Draw one side panel (name, score, move table) at horizontal offset x0."""
        bg[:, x0:x0 + SIDEBAR_W] = PANEL_BG

        name  = self._logger.player_names[color]
        moves = self._logger.moves[color]
        score = self._logger.score[color]

        _txt(bg, name,           x0 + 10, 40, scale=0.7,  color=GOLD,              bold=True)
        _txt(bg, f"Score: {score}", x0 + 10, 68, scale=0.55, color=(0, 255, 100, 255), bold=True)
        self._draw_move_table(bg, x0, moves, header_y=100)

    # ------------------------------------------------------------------ #
    #  Board coordinates                                                   #
    # ------------------------------------------------------------------ #

    def _draw_coordinates(self, bg):
        """Draw a-h along the bottom and 1-8 along the sides of the board."""
        for i in range(8):
            # Column letters (bottom)
            cx = BOARD_X + i * CELL_SIZE + CELL_SIZE // 2 - 7
            _txt(bg, COL_LETTERS[i], cx, BOARD_Y + BOARD_SIZE + COORD_SIZE - 5,
                 scale=0.5, color=GRAY_TXT)
            # Row numbers (left side)
            ry = BOARD_Y + i * CELL_SIZE + CELL_SIZE // 2 + 6
            _txt(bg, str(8 - i), BOARD_X - COORD_SIZE + 5, ry,
                 scale=0.5, color=GRAY_TXT)

    # ------------------------------------------------------------------ #
    #  Main draw                                                           #
    # ------------------------------------------------------------------ #

    def _draw_pieces(self, canvas: Img, board: Board, state: GameState):
        """Draw all stationary, moving, and airborne pieces onto the canvas."""
        self._draw_stationary(canvas, board, state)
        self._draw_moving(canvas, board, state)
        self._draw_airborne(canvas, board, state)

    def _draw_stationary(self, canvas: Img, board: Board, state: GameState):
        """Draw pieces that are not currently in motion."""
        moving_sources = {m.source for m in state.pending_moves}
        for row in range(len(board.matrix)):
            for col in range(len(board.matrix[row])):
                pos   = Position(row, col)
                piece = board.get_piece(pos)
                if piece is None or pos in moving_sources:
                    continue
                self._draw_stationary_piece(canvas, pos, piece, state)

    def _draw_stationary_piece(self, canvas: Img, pos: Position, piece, state: GameState):
        """Resolve sprite frame and draw a single stationary piece."""
        sheet = get_sprite_sheet(piece)
        s     = piece_state(pos, state)
        start = _state_start(pos, s, state)
        frame = sheet.get_frame(s, state.current_time, start)
        x, y  = _pos_to_px(pos)
        frame.draw_on(canvas, x, y)

    def _draw_moving(self, canvas: Img, board: Board, state: GameState):
        """Draw pieces that are currently travelling to their target."""
        for move in state.pending_moves:
            piece = board.get_piece(move.source)
            if piece is None:
                continue
            sheet    = get_sprite_sheet(piece)
            distance = max(abs(move.target.row - move.source.row),
                           abs(move.target.col - move.source.col))
            start    = move.arrival - MOVE_DURATION * distance
            frame    = sheet.get_frame("move", state.current_time, start)
            x, y     = _interpolated_px(move, state.current_time)
            frame.draw_on(canvas, x, y)

    def _draw_airborne(self, canvas: Img, board: Board, state: GameState):
        """Draw pieces that are currently airborne (jump animation)."""
        for airborne in state.airborne:
            piece = board.get_piece(airborne.cell)
            if piece is None:
                continue
            sheet = get_sprite_sheet(piece)
            start = airborne.landing_time - MOVE_DURATION
            frame = sheet.get_frame("jump", state.current_time, start)
            x, y  = _pos_to_px(airborne.cell)
            frame.draw_on(canvas, x, y)

    def _draw_selection(self, bg, selected: Position | None):
        """Highlight the selected cell with a semi-transparent overlay."""
        if selected is None:
            return
        x, y = _pos_to_px(selected)
        overlay = bg.copy()
        cv2.rectangle(overlay, (x, y), (x + CELL_SIZE, y + CELL_SIZE), (0, 255, 255, 180), -1)
        cv2.addWeighted(overlay, 0.35, bg, 0.65, 0, bg)

    def _draw_game_over(self, canvas: Img, state: GameState):
        """Overlay GAME OVER text if the game has ended."""
        if state.game_over:
            canvas.put_text("GAME OVER", BOARD_X + 150, BOARD_Y + 400, 2.5, (0, 0, 255, 255), 4)

    def draw(self, board: Board, state: GameState, selected: Position | None) -> Img:
        canvas     = Img()
        canvas.img = np.full((CANVAS_H, CANVAS_W, 4), DARK_BG, dtype=np.uint8)
        bg         = canvas.img

        bg[BOARD_Y:BOARD_Y + BOARD_SIZE, BOARD_X:BOARD_X + BOARD_SIZE] = self._board_bg.img
        self._draw_coordinates(bg)
        self._draw_panel(bg, 0, Color.BLACK)
        self._draw_panel(bg, SIDEBAR_W + COORD_SIZE + BOARD_SIZE + COORD_SIZE, Color.WHITE)
        self._draw_selection(bg, selected)
        self._draw_pieces(canvas, board, state)
        self._draw_game_over(canvas, state)
        return canvas

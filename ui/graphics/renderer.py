import numpy as np
import cv2
from dataclasses import dataclass
from ui.graphics.img import Img
from ui.graphics.theme import SIDEBAR_W, COORD_SIZE, FONT, DARK_BG, GRAY_TXT, WHITE_TXT
from ui.graphics.panel_renderer import PanelRenderer
from ui.graphics.piece_renderer import PieceRenderer
from core.model.board import Board
from core.model.game_state import GameState
from core.model.position import Position
from core.model.piece import Color
from core.rules.rule_engine import RuleEngine
from constants import MIN_CELL_SIZE, MAX_CELL_SIZE, BOARD_IMAGE

COL_LETTERS = "ABCDEFGH"


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


def _txt(bg, text, x, y, scale=0.5, color=WHITE_TXT, bold=False):
    cv2.putText(bg, text, (x, y), FONT, scale, color, 2 if bold else 1, cv2.LINE_AA)


class _NullMoveLogger:
    """Null Object — used when no logger is provided."""
    def __init__(self):
        self.player_names = {Color.WHITE: "White", Color.BLACK: "Black"}
        self.moves        = {Color.WHITE: [],      Color.BLACK: []}
        self.score        = {Color.WHITE: 0,       Color.BLACK: 0}


class Renderer:
    def __init__(self, move_logger=None):
        logger           = move_logger or _NullMoveLogger()
        self._panel      = PanelRenderer(logger)
        self._pieces     = PieceRenderer()
        self._rules      = RuleEngine()
        self._last_cell  = None
        self._board_bg   = None

    def _get_board_bg(self, layout: Layout) -> Img:
        if layout.cell_size != self._last_cell:
            self._board_bg  = Img().read(str(BOARD_IMAGE), size=(layout.board_size, layout.board_size))
            self._last_cell = layout.cell_size
        return self._board_bg

    def _draw_coordinates(self, bg, layout: Layout):
        for i in range(8):
            cx = layout.board_x + i * layout.cell_size + layout.cell_size // 2 - 7
            _txt(bg, COL_LETTERS[i], cx, layout.board_y + layout.board_size + COORD_SIZE - 5,
                 scale=0.5, color=GRAY_TXT)
            ry = layout.board_y + i * layout.cell_size + layout.cell_size // 2 + 6
            _txt(bg, str(8 - i), layout.board_x - COORD_SIZE + 5, ry, scale=0.5, color=GRAY_TXT)

    def _draw_selection(self, bg, selected: Position | None, layout: Layout):
        if selected is None:
            return
        x = layout.board_x + selected.col * layout.cell_size
        y = layout.board_y + selected.row * layout.cell_size
        overlay = bg.copy()
        cv2.rectangle(overlay, (x, y), (x + layout.cell_size, y + layout.cell_size), (0, 255, 255, 180), -1)
        cv2.addWeighted(overlay, 0.35, bg, 0.65, 0, bg)

    def _draw_legal_moves(self, bg, board: Board, selected: Position, layout: Layout):
        piece = board.get_piece(selected)
        if piece is None:
            return
        for target in self._rules.legal_targets(piece, selected, board):
            x = layout.board_x + target.col * layout.cell_size
            y = layout.board_y + target.row * layout.cell_size
            if board.get_piece(target) is not None:
                # Capture — translucent red square over the threatened piece
                overlay = bg.copy()
                cv2.rectangle(overlay, (x, y), (x + layout.cell_size, y + layout.cell_size),
                              (0, 0, 255, 200), -1)
                cv2.addWeighted(overlay, 0.35, bg, 0.65, 0, bg)
            else:
                # Empty square — small dot marking a reachable move
                cx = x + layout.cell_size // 2
                cy = y + layout.cell_size // 2
                cv2.circle(bg, (cx, cy), layout.cell_size // 8, (60, 200, 60, 220), -1)

    def _draw_game_over(self, canvas: Img, state: GameState, layout: Layout):
        if state.game_over:
            canvas.put_text("GAME OVER", layout.board_x + layout.board_size // 4,
                            layout.board_y + layout.board_size // 2,
                            layout.cell_size / 40, (0, 0, 255, 255), 4)

    def draw(self, board: Board, state: GameState,
             selected: Position | None, cell_size: int) -> tuple:
        layout     = make_layout(cell_size)
        canvas     = Img()
        canvas.img = np.full((layout.canvas_h, layout.canvas_w, 4), DARK_BG, dtype=np.uint8)
        bg         = canvas.img

        board_bg = self._get_board_bg(layout)
        bg[layout.board_y:layout.board_y + layout.board_size,
           layout.board_x:layout.board_x + layout.board_size] = board_bg.img

        self._draw_coordinates(bg, layout)
        self._panel.draw(bg, 0, Color.BLACK, layout)
        self._panel.draw(bg, SIDEBAR_W + COORD_SIZE + layout.board_size + COORD_SIZE, Color.WHITE, layout)
        self._draw_selection(bg, selected, layout)
        if selected is not None:
            self._draw_legal_moves(bg, board, selected, layout)
        self._pieces.draw_all(canvas, board, state, layout)
        self._draw_game_over(canvas, state, layout)
        return canvas, layout

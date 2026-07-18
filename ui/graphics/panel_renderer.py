import cv2
from core.model.piece import Color
from ui.graphics.theme import SIDEBAR_W, FONT, GOLD, WHITE_TXT, GRAY_TXT, DIVIDER, PANEL_BG


def _txt(bg, text, x, y, scale=0.5, color=WHITE_TXT, bold=False):
    cv2.putText(bg, text, (x, y), FONT, scale, color, 2 if bold else 1, cv2.LINE_AA)


class PanelRenderer:
    def __init__(self, move_logger):
        self._logger = move_logger

    def draw(self, bg, x0: int, color: Color, layout):
        bg[:, x0:x0 + SIDEBAR_W] = PANEL_BG
        name  = self._logger.player_names[color]
        moves = self._logger.moves[color]
        score = self._logger.score[color]
        _txt(bg, name,              x0 + 10, 40, scale=0.7,  color=GOLD,            bold=True)
        _txt(bg, f"Score: {score}", x0 + 10, 68, scale=0.55, color=(0, 255, 100, 255), bold=True)
        self._draw_headers(bg, x0, header_y=100)
        self._draw_rows(bg, x0, moves, header_y=100, layout=layout)

    def _draw_headers(self, bg, x0: int, header_y: int):
        cv2.line(bg, (x0 + 5, header_y - 5), (x0 + SIDEBAR_W - 5, header_y - 5), DIVIDER, 1)
        _txt(bg, "Time", x0 + 10,  header_y, scale=0.45, color=GRAY_TXT)
        _txt(bg, "Move", x0 + 155, header_y, scale=0.45, color=GRAY_TXT)
        cv2.line(bg, (x0 + 5, header_y + 8), (x0 + SIDEBAR_W - 5, header_y + 8), DIVIDER, 1)

    def _draw_rows(self, bg, x0: int, moves: list, header_y: int, layout):
        max_rows = (layout.board_size - 120) // 26
        for i, (t, m) in enumerate(moves[-max_rows:]):
            y = header_y + 25 + i * 26
            if y > layout.board_y + layout.board_size - 20:
                break
            bg[y - 16:y + 8, x0 + 5:x0 + SIDEBAR_W - 5] = (50, 50, 70, 255) if i % 2 == 0 else PANEL_BG
            _txt(bg, t, x0 + 10,  y, scale=0.42, color=WHITE_TXT)
            _txt(bg, m, x0 + 155, y, scale=0.45, color=GOLD)

import cv2
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_builder import GameBuilder
from graphics.renderer import Renderer, BOARD_X, BOARD_Y
from events.move_logger import MoveLogger
from input.board_mapper import pixel_to_pos
from constants import CELL_SIZE

WINDOW = "Kung-Fu Chess"

DEFAULT_BOARD = [
    "bR bN bB bQ bK bB bN bR",
    "bP bP bP bP bP bP bP bP",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    "wP wP wP wP wP wP wP wP",
    "wR wN wB wQ wK wB wN wR",
]


def run():
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    app = builder.build()
    engine = app.engine
    controller = app.controller
    move_logger = MoveLogger(engine.board, white_name="White", black_name="Black")
    engine.add_listener(move_logger)
    renderer = Renderer(move_logger)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            controller.click(x, y, CELL_SIZE, BOARD_X, BOARD_Y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            engine.request_jump(pixel_to_pos(x, y, CELL_SIZE, BOARD_X, BOARD_Y))

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_mouse)

    last = time.perf_counter()
    while True:
        now = time.perf_counter()
        elapsed_ms = int((now - last) * 1000)
        last = now

        engine.advance_time(elapsed_ms)
        move_logger.tick(engine.state.current_time)
        canvas = renderer.draw(engine.board, engine.state, controller._selected)
        frame = cv2.cvtColor(canvas.img, cv2.COLOR_BGRA2BGR)
        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cv2.destroyAllWindows()

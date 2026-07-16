import cv2
import time
from engine.game_builder import GameBuilder
from graphics.renderer import Renderer, _make_layout, MIN_CELL_SIZE, MAX_CELL_SIZE
from events.move_logger import MoveLogger
from input.board_mapper import pixel_to_pos
from constants import CELL_SIZE

WINDOW       = "Kung-Fu Chess"
ZOOM_STEP    = 5   # pixels per +/- keypress

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


def _cell_size_from_window(window: str, fallback: int) -> int:
    """Derive cell_size from the current window height, clamped to valid range."""
    rect = cv2.getWindowImageRect(window)
    if rect is None or rect[3] <= 0:
        return fallback
    # canvas_h = COORD_SIZE + cell_size*8 + COORD_SIZE  =>  cell_size = (h - 60) // 8
    cell_size = (rect[3] - 60) // 8
    return max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, cell_size))


def run():
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    app        = builder.build()
    engine     = app.engine
    controller = app.controller
    move_logger = MoveLogger(engine.board, white_name="White", black_name="Black")
    engine.add_listener(move_logger)
    renderer   = Renderer(move_logger)

    cell_size  = CELL_SIZE
    layout     = _make_layout(cell_size)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            controller.click(x, y, layout.cell_size, layout.board_x, layout.board_y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            engine.request_jump(pixel_to_pos(x, y, layout.cell_size, layout.board_x, layout.board_y))

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.setMouseCallback(WINDOW, on_mouse)

    last = time.perf_counter()
    while True:
        now        = time.perf_counter()
        elapsed_ms = int((now - last) * 1000)
        last       = now

        engine.advance_time(elapsed_ms)
        move_logger.tick(engine.state.current_time)

        # Recalculate cell_size from actual window size each frame
        cell_size = _cell_size_from_window(WINDOW, cell_size)
        canvas, layout = renderer.draw(engine.board, engine.state, controller._selected, cell_size)

        frame = cv2.cvtColor(canvas.img, cv2.COLOR_BGRA2BGR)
        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('+') or key == ord('='):
            cell_size = min(cell_size + ZOOM_STEP, MAX_CELL_SIZE)
        elif key == ord('-'):
            cell_size = max(cell_size - ZOOM_STEP, MIN_CELL_SIZE)

    cv2.destroyAllWindows()

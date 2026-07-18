import cv2
import time
import numpy as np
from core.engine.game_builder import GameBuilder
from ui.graphics.renderer import Renderer, make_layout
from core.events.move_logger import MoveLogger
from ui.server_bridge.local_bridge import LocalBridge
from ui.state.state_manager import StateManager
from ui.state.menu_state import MenuState
from ui.state.game_ui_state import GameUIState
from ui.state.game_over_state import GameOverState
from constants import CELL_SIZE, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP
from ui.graphics.theme import DARK_BG

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


def _cell_size_from_window(window: str, fallback: int) -> int:
    rect = cv2.getWindowImageRect(window)
    if rect is None or rect[3] <= 0:
        return fallback
    cell_size = (rect[3] - 60) // 8
    return max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, cell_size))


def _build_bridge() -> tuple:
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    app         = builder.build()
    move_logger = MoveLogger(app.engine.board, white_name="White", black_name="Black")
    app.engine.add_listener(move_logger)
    bridge      = LocalBridge(app.engine)
    return bridge, app.controller, move_logger


def run():
    cell_size = CELL_SIZE
    layout    = make_layout(cell_size)

    bridge, controller, move_logger = _build_bridge()
    renderer = Renderer(move_logger)

    def start_game():
        nonlocal manager
        manager.transition(GameUIState(bridge))

    def restart():
        nonlocal bridge, controller, move_logger, renderer, manager
        bridge, controller, move_logger = _build_bridge()
        renderer = Renderer(move_logger)
        manager.transition(GameUIState(bridge))

    def quit_game():
        raise SystemExit

    manager = StateManager(MenuState(start_game, quit_game,
                                     layout.canvas_w, layout.canvas_h))

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            current = manager.current
            if isinstance(current, GameUIState):
                controller.click(x, y, layout.cell_size, layout.board_x, layout.board_y)
            else:
                manager.handle_input({"type": "click", "x": x, "y": y})
        elif event == cv2.EVENT_RBUTTONDOWN:
            if isinstance(manager.current, GameUIState):
                controller.jump(x, y, layout.cell_size, layout.board_x, layout.board_y)

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.setMouseCallback(WINDOW, on_mouse)

    last = time.perf_counter()
    while True:
        now        = time.perf_counter()
        elapsed_ms = int((now - last) * 1000)
        last       = now

        try:
            manager.update(elapsed_ms)
        except SystemExit:
            break

        cell_size = _cell_size_from_window(WINDOW, cell_size)

        # Check game over transition
        if isinstance(manager.current, GameUIState) and bridge.get_state().game_over:
            manager.transition(GameOverState(restart, quit_game,
                                             layout.canvas_w, layout.canvas_h))

        current = manager.current
        if isinstance(current, GameUIState):
            move_logger.tick(bridge.get_state().current_time)
            canvas, layout = renderer.draw(bridge.get_board(), bridge.get_state(),
                                           controller._selected, cell_size)
            frame = cv2.cvtColor(canvas.img, cv2.COLOR_BGRA2BGR)
        else:
            layout    = make_layout(cell_size)
            bg        = np.full((layout.canvas_h, layout.canvas_w, 3), DARK_BG[:3], dtype=np.uint8)
            current.draw(bg)
            frame = bg

        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('+') or key == ord('='):
            new_cell = min(cell_size + ZOOM_STEP, MAX_CELL_SIZE)
            cv2.resizeWindow(WINDOW, make_layout(new_cell).canvas_w, make_layout(new_cell).canvas_h)
        elif key == ord('-'):
            new_cell = max(cell_size - ZOOM_STEP, MIN_CELL_SIZE)
            cv2.resizeWindow(WINDOW, make_layout(new_cell).canvas_w, make_layout(new_cell).canvas_h)

    cv2.destroyAllWindows()

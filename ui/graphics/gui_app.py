import cv2
import time
import numpy as np
from core.engine.game_builder import GameBuilder
from ui.graphics.renderer import Renderer, make_layout
from core.events.move_logger import MoveLogger
from ui.sound.sound_manager import SoundManager
from ui.server_bridge.local_bridge import LocalBridge
from ui.server_bridge.ws_bridge import WebSocketBridge
from ui.state.state_manager import StateManager
from ui.state.menu_state import MenuState
from ui.state.game_ui_state import GameUIState
from ui.state.game_over_state import GameOverState
from constants import CELL_SIZE, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP, DEFAULT_BOARD
from ui.graphics.theme import DARK_BG

WINDOW = "Kung-Fu Chess"


def _cell_size_from_window(window: str, fallback: int) -> int:
    """
    Derive the board cell size (px) from the current window height.

    Subtracts 60 px for the top + bottom coordinate labels (COORD_SIZE * 2),
    then divides by 8 board rows. The result is clamped to [MIN_CELL_SIZE, MAX_CELL_SIZE].
    Returns `fallback` if the window does not exist yet or reports an invalid size.
    """
    rect = cv2.getWindowImageRect(window)
    if rect is None or rect[3] <= 0:
        return fallback
    cell_size = (rect[3] - 60) // 8
    return max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, cell_size))


def _build_bridge(use_ws: bool = False) -> tuple:
    """
    Build a complete, fresh game session from DEFAULT_BOARD.
    use_ws=True  → WebSocketBridge (talks to game_server.py)
    use_ws=False → LocalBridge     (engine runs in-process)
    """
    builder = GameBuilder()
    for row in DEFAULT_BOARD:
        builder.with_row(row)
    app = builder.build()
    move_logger = MoveLogger(app.engine.board, app.engine.bus, white_name="White", black_name="Black")
    SoundManager(app.engine.bus)
    if use_ws:
        bridge = WebSocketBridge(app.engine.bus)
        bridge.connect()
    else:
        bridge = LocalBridge(app.engine)
    return bridge, app.controller, move_logger


def _render_frame(manager, bridge, controller, move_logger, renderer, cell_size) -> tuple:
    """Render one frame; returns (frame_bgr, layout)."""
    current = manager.current
    if isinstance(current, GameUIState):
        move_logger.tick(bridge.get_state().current_time)
        canvas, layout = renderer.draw(bridge.get_board(), bridge.get_state(),
                                       controller._selected, cell_size)
        return cv2.cvtColor(canvas.img, cv2.COLOR_BGRA2BGR), layout
    layout = make_layout(cell_size)
    bg = np.full((layout.canvas_h, layout.canvas_w, 3), DARK_BG[:3], dtype=np.uint8)
    current.draw(bg)
    return bg, layout


def _handle_zoom(key: int, cell_size: int) -> int:
    """Return updated cell_size after zoom key press (+/=/-)."""
    if key == ord('+') or key == ord('='):
        new_cell = min(cell_size + ZOOM_STEP, MAX_CELL_SIZE)
    elif key == ord('-'):
        new_cell = max(cell_size - ZOOM_STEP, MIN_CELL_SIZE)
    else:
        return cell_size
    cv2.resizeWindow(WINDOW, make_layout(new_cell).canvas_w, make_layout(new_cell).canvas_h)
    return new_cell


def _run_loop(manager, bridge, controller, move_logger, renderer, cell_size, use_ws, restart, quit_game):
    """Run the ~60 fps game loop until the user quits."""
    last = time.perf_counter()
    while True:
        now = time.perf_counter()
        elapsed_ms = int((now - last) * 1000)
        last = now

        try:
            manager.update(elapsed_ms)
        except SystemExit:
            break

        cell_size = _cell_size_from_window(WINDOW, cell_size)

        if isinstance(manager.current, GameUIState) and bridge.get_state().game_over:
            layout = make_layout(cell_size)
            manager.transition(GameOverState(restart, quit_game,
                                             layout.canvas_w, layout.canvas_h))

        frame, _ = _render_frame(manager, bridge, controller, move_logger, renderer, cell_size)
        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        cell_size = _handle_zoom(key, cell_size)

    cv2.destroyAllWindows()


def run(use_ws: bool = False):
    """Main GUI entry point — creates the OpenCV window and runs the ~60 fps game loop."""
    cell_size = CELL_SIZE
    layout = make_layout(cell_size)

    bridge, controller, move_logger = _build_bridge(use_ws)
    renderer = Renderer(move_logger)

    def start_game():
        nonlocal manager
        manager.transition(GameUIState(bridge))

    def restart():
        nonlocal bridge, controller, move_logger, renderer, manager
        bridge, controller, move_logger = _build_bridge(use_ws)
        renderer = Renderer(move_logger)
        manager.transition(GameUIState(bridge))

    def quit_game():
        raise SystemExit

    manager = StateManager(MenuState(start_game, quit_game, layout.canvas_w, layout.canvas_h))

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

    _run_loop(manager, bridge, controller, move_logger, renderer, cell_size, use_ws, restart, quit_game)

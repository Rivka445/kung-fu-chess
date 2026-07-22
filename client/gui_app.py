import cv2
import time
import numpy as np
from client.graphics.renderer import Renderer, make_layout
from client.session import build_bridge, build_move_logger_for_match
from client.state.state_manager import StateManager
from client.state.menu_state import MenuState
from client.state.searching_state import SearchingState
from client.state.no_match_state import NoMatchState
from client.state.game_ui_state import GameUIState
from client.state.game_over_state import GameOverState
from shared.constants.constants import CELL_SIZE, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP
from client.graphics.theme import DARK_BG

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


def run(username: str = "Player"):
    """Main GUI entry point — creates the OpenCV window and runs the ~60 fps game loop."""
    cell_size = CELL_SIZE
    layout = make_layout(cell_size)

    bridge, controller, move_logger, game_over_watch, match_found_watch, bus = build_bridge(username)
    renderer = Renderer(move_logger)

    def start_game():
        nonlocal manager
        manager.transition(GameUIState(bridge))

    def start_search():
        nonlocal manager
        match_found_watch.matched = False
        game_over_watch.game_over = False
        manager.transition(SearchingState(bridge, layout.canvas_w, layout.canvas_h))

    def quit_game():
        raise SystemExit

    def back_to_menu():
        nonlocal manager
        manager.transition(MenuState(start_game, quit_game, layout.canvas_w, layout.canvas_h,
                                     on_play=start_search))

    def restart():
        # Same, already-authenticated connection — just search again.
        match_found_watch.matched = False
        game_over_watch.game_over = False
        manager.transition(SearchingState(bridge, layout.canvas_w, layout.canvas_h))

    manager = StateManager(MenuState(start_game, quit_game, layout.canvas_w, layout.canvas_h,
                                     on_play=start_search))

    cell_size_ref = [cell_size]  # mutable container so on_mouse can read current value

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            current = manager.current
            if isinstance(current, GameUIState):
                cur_layout = make_layout(cell_size_ref[0])
                controller.click(x, y, cur_layout.cell_size, cur_layout.board_x, cur_layout.board_y)
            else:
                manager.handle_input({"type": "click", "x": x, "y": y})
        elif event == cv2.EVENT_RBUTTONDOWN:
            if isinstance(manager.current, GameUIState):
                cur_layout = make_layout(cell_size_ref[0])
                controller.jump(x, y, cur_layout.cell_size, cur_layout.board_x, cur_layout.board_y)

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.setMouseCallback(WINDOW, on_mouse)

    def _run_loop():
        """
        Run the ~60 fps game loop until the user quits.
        Nested so it can rebind move_logger/renderer via nonlocal once a WS match
        is found — a plain (non-nested) function taking them as parameters would
        keep rendering the stale, pre-match placeholders.
        """
        nonlocal cell_size, move_logger, renderer
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
            cell_size_ref[0] = cell_size

            if isinstance(manager.current, SearchingState) and match_found_watch.matched:
                move_logger = build_move_logger_for_match(bridge, bus, username)
                renderer = Renderer(move_logger)
                manager.transition(GameUIState(bridge))
            elif isinstance(manager.current, SearchingState) and bridge.search_status == "timed_out":
                cur_layout = make_layout(cell_size)
                manager.transition(NoMatchState(back_to_menu, cur_layout.canvas_w, cur_layout.canvas_h))
            elif isinstance(manager.current, GameUIState) and game_over_watch.game_over:
                cur_layout = make_layout(cell_size)
                manager.transition(GameOverState(restart, quit_game,
                                                 cur_layout.canvas_w, cur_layout.canvas_h))

            frame, _ = _render_frame(manager, bridge, controller, move_logger, renderer, cell_size)
            cv2.imshow(WINDOW, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            cell_size = _handle_zoom(key, cell_size)

        cv2.destroyAllWindows()

    _run_loop()

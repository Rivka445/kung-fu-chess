import cv2
import time
import numpy as np
from core.engine.game_builder import GameBuilder
from core.events.event_bus import EventBus
from ui.graphics.renderer import Renderer, make_layout
from core.events.move_logger import MoveLogger
from ui.sound.sound_manager import SoundManager
from ui.server_bridge.local_bridge import LocalBridge
from ui.server_bridge.ws_bridge import WebSocketBridge
from ui.input.controller import Controller
from ui.state.state_manager import StateManager
from ui.state.menu_state import MenuState
from ui.state.game_ui_state import GameUIState
from ui.state.game_over_state import GameOverState
from constants import CELL_SIZE, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP, DEFAULT_BOARD
from ui.graphics.theme import DARK_BG
from core.model.piece import Color

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


def _build_bridge(use_ws: bool = False, white_name: str = "White", black_name: str = "Black") -> tuple:
    if use_ws:
        # WS mode: the server owns the real GameEngine/RuleEngine — this process
        # never builds one. It only mirrors the state the server sends and renders it,
        # via a plain EventBus for local listeners (sound, move log) to subscribe to.
        #
        # main.py passes the local player's own username as both white_name and
        # black_name — the server decides who is actually White or Black based on
        # join order. Compare against the server's answer to mark which side is "you"
        # in the sidebar.
        bus = EventBus()
        bridge = WebSocketBridge(bus, username=white_name)
        bridge.connect()
        my_name = white_name
        server_white, server_black = bridge.player_names[Color.WHITE], bridge.player_names[Color.BLACK]
        move_logger = MoveLogger(bridge.get_board(), bus,
                                 white_name=server_white + (" (You)" if server_white == my_name else ""),
                                 black_name=server_black + (" (You)" if server_black == my_name else ""))
    else:
        # Local (hot-seat) mode: no server exists, so this process runs the real
        # GameEngine itself.
        builder = GameBuilder()
        for row in DEFAULT_BOARD:
            builder.with_row(row)
        app = builder.build()
        bus = app.engine.bus
        bridge = LocalBridge(app.engine)
        move_logger = MoveLogger(app.engine.board, bus,
                                 white_name=white_name, black_name=black_name)
    SoundManager(bus)
    controller = Controller(bridge)
    if not use_ws:
        # All local listeners are wired now — safe to announce game start.
        app.engine.start()
    return bridge, controller, move_logger


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


def _run_loop(manager, bridge, controller, move_logger, renderer, cell_size, cell_size_ref, use_ws, restart, quit_game):
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
        cell_size_ref[0] = cell_size

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


def run(use_ws: bool = False, white_name: str = "White", black_name: str = "Black"):
    """Main GUI entry point — creates the OpenCV window and runs the ~60 fps game loop."""
    cell_size = CELL_SIZE
    layout = make_layout(cell_size)

    bridge, controller, move_logger = _build_bridge(use_ws, white_name, black_name)
    renderer = Renderer(move_logger)

    def start_game():
        nonlocal manager
        manager.transition(GameUIState(bridge))

    def restart():
        nonlocal bridge, controller, move_logger, renderer, manager
        bridge, controller, move_logger = _build_bridge(use_ws, white_name, black_name)
        renderer = Renderer(move_logger)
        manager.transition(GameUIState(bridge))

    def quit_game():
        raise SystemExit

    manager = StateManager(MenuState(start_game, quit_game, layout.canvas_w, layout.canvas_h))

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

    _run_loop(manager, bridge, controller, move_logger, renderer, cell_size, cell_size_ref, use_ws, restart, quit_game)

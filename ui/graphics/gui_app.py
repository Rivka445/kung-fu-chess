import cv2
import time
import numpy as np
from core.engine.game_builder import GameBuilder
from core.events.event_bus import EventBus, GameStarted, GameOver
from ui.graphics.renderer import Renderer, make_layout
from core.events.move_logger import MoveLogger
from ui.sound.sound_manager import SoundManager
from ui.server_bridge.local_bridge import LocalBridge
from ui.server_bridge.ws_bridge import WebSocketBridge
from ui.input.controller import Controller
from ui.state.state_manager import StateManager
from ui.state.menu_state import MenuState
from ui.state.searching_state import SearchingState
from ui.state.no_match_state import NoMatchState
from ui.state.game_ui_state import GameUIState
from ui.state.game_over_state import GameOverState
from constants import CELL_SIZE, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP, DEFAULT_BOARD
from ui.graphics.theme import DARK_BG
from core.model.piece import Color

WINDOW = "Kung-Fu Chess"


class _GameOverWatch:
    """
    Bus-driven game-over flag, replacing per-frame polling of bridge state.
    In WS mode the GameOver event may arrive on the WebSocketBridge's
    background recv thread, so this only ever sets a flag here — the actual
    state-machine transition still happens on the main render loop thread.
    """
    def __init__(self, bus: EventBus):
        self.game_over = False
        bus.subscribe(GameOver, lambda e: setattr(self, "game_over", True))


class _MatchFoundWatch:
    """
    Bus-driven "matched" flag, mirroring _GameOverWatch. GameStarted is
    published by the server once matchmaking pairs two players, and arrives
    on the WebSocketBridge's background recv thread — this just sets a flag
    for the main render loop to notice and transition out of SearchingState.
    """
    def __init__(self, bus: EventBus):
        self.matched = False
        bus.subscribe(GameStarted, lambda e: setattr(self, "matched", True))


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
        # Only login happens here — matchmaking is deferred until the player clicks
        # Play (SearchingState calls bridge.start_search()). Player names aren't known
        # until a match is found, so move_logger is built later too (see
        # _build_move_logger_for_match), once GameStarted fires.
        bus = EventBus()
        bridge = WebSocketBridge(bus, username=white_name)
        bridge.login()
        move_logger = None
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
    game_over_watch = _GameOverWatch(bus)
    match_found_watch = _MatchFoundWatch(bus)
    controller = Controller(bridge)
    if not use_ws:
        # All local listeners are wired now — safe to announce game start.
        app.engine.start()
    return bridge, controller, move_logger, game_over_watch, match_found_watch, bus


def _build_move_logger_for_match(bridge: WebSocketBridge, bus: EventBus, my_name: str) -> MoveLogger:
    """Build the MoveLogger once a WS match is found and player names/colors are known."""
    server_white, server_black = bridge.player_names[Color.WHITE], bridge.player_names[Color.BLACK]
    return MoveLogger(bridge.get_board(), bus,
                      white_name=server_white + (" (You)" if server_white == my_name else ""),
                      black_name=server_black + (" (You)" if server_black == my_name else ""))


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


def run(use_ws: bool = False, white_name: str = "White", black_name: str = "Black"):
    """Main GUI entry point — creates the OpenCV window and runs the ~60 fps game loop."""
    cell_size = CELL_SIZE
    layout = make_layout(cell_size)

    bridge, controller, move_logger, game_over_watch, match_found_watch, bus = _build_bridge(
        use_ws, white_name, black_name)
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
                                     on_play=start_search if use_ws else None))

    def restart():
        nonlocal bridge, controller, move_logger, renderer, manager, game_over_watch, match_found_watch, bus
        if use_ws:
            # Same, already-authenticated connection — just search again.
            match_found_watch.matched = False
            game_over_watch.game_over = False
            manager.transition(SearchingState(bridge, layout.canvas_w, layout.canvas_h))
        else:
            bridge, controller, move_logger, game_over_watch, match_found_watch, bus = _build_bridge(
                use_ws, white_name, black_name)
            renderer = Renderer(move_logger)
            manager.transition(GameUIState(bridge))

    manager = StateManager(MenuState(start_game, quit_game, layout.canvas_w, layout.canvas_h,
                                     on_play=start_search if use_ws else None))

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
        Nested so it always sees the latest bridge/controller/renderer/game_over_watch —
        restart() rebinds those via nonlocal, and a plain (non-nested) function taking
        them as parameters would keep rendering the stale, already-finished game.
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
                move_logger = _build_move_logger_for_match(bridge, bus, white_name)
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

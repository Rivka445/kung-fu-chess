import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from client import gui_app
from client.state.game_ui_state import GameUIState
from client.state.menu_state import MenuState
from client.graphics.renderer import Renderer, make_layout
from client.engine_bridge.local_bridge import LocalBridge
from client.input.controller import Controller
from server.game.engine.game_engine import GameEngine
from server.game.rules.rule_engine import RuleEngine
from shared.model.board import Board
from server.utils.board_parser import parse_row
from shared.constants.constants import DEFAULT_BOARD, MIN_CELL_SIZE, MAX_CELL_SIZE, ZOOM_STEP


def _default_board():
    board = Board()
    for row in DEFAULT_BOARD:
        board.add_parsed_row(parse_row(row, board.expected_cols))
    return board


# ---- _cell_size_from_window ----

def test_cell_size_from_window_derives_from_height(monkeypatch):
    monkeypatch.setattr(gui_app.cv2, "getWindowImageRect", lambda window: (0, 0, 800, 860))
    # (860 - 60) // 8 == 100
    assert gui_app._cell_size_from_window("W", fallback=77) == 100


def test_cell_size_from_window_falls_back_when_no_window(monkeypatch):
    monkeypatch.setattr(gui_app.cv2, "getWindowImageRect", lambda window: None)
    assert gui_app._cell_size_from_window("W", fallback=77) == 77

    monkeypatch.setattr(gui_app.cv2, "getWindowImageRect", lambda window: (0, 0, 0, -1))
    assert gui_app._cell_size_from_window("W", fallback=77) == 77


def test_cell_size_from_window_clamps_to_bounds(monkeypatch):
    monkeypatch.setattr(gui_app.cv2, "getWindowImageRect", lambda window: (0, 0, 10, 10))
    assert gui_app._cell_size_from_window("W", fallback=77) == MIN_CELL_SIZE

    monkeypatch.setattr(gui_app.cv2, "getWindowImageRect", lambda window: (0, 0, 5000, 5000))
    assert gui_app._cell_size_from_window("W", fallback=77) == MAX_CELL_SIZE


# ---- _handle_zoom ----

def test_handle_zoom_plus_increases_and_resizes_window(monkeypatch):
    calls = []
    monkeypatch.setattr(gui_app.cv2, "resizeWindow", lambda *a: calls.append(a))
    result = gui_app._handle_zoom(ord('+'), 100)
    assert result == 100 + ZOOM_STEP
    assert len(calls) == 1


def test_handle_zoom_minus_decreases(monkeypatch):
    monkeypatch.setattr(gui_app.cv2, "resizeWindow", lambda *a: None)
    result = gui_app._handle_zoom(ord('-'), 100)
    assert result == 100 - ZOOM_STEP


def test_handle_zoom_clamps_to_bounds(monkeypatch):
    monkeypatch.setattr(gui_app.cv2, "resizeWindow", lambda *a: None)
    assert gui_app._handle_zoom(ord('+'), MAX_CELL_SIZE) == MAX_CELL_SIZE
    assert gui_app._handle_zoom(ord('-'), MIN_CELL_SIZE) == MIN_CELL_SIZE


def test_handle_zoom_other_key_leaves_cell_size_untouched(monkeypatch):
    calls = []
    monkeypatch.setattr(gui_app.cv2, "resizeWindow", lambda *a: calls.append(a))
    assert gui_app._handle_zoom(ord('q'), 100) == 100
    assert calls == []


# ---- _render_frame ----

def test_render_frame_game_ui_state_ticks_logger_and_returns_bgr_canvas():
    board = _default_board()
    engine = GameEngine(board, RuleEngine())
    engine.start()
    bridge = LocalBridge(engine)
    controller = Controller(bridge)
    state = GameUIState(bridge)

    class FakeManager:
        current = state

    from shared.model.piece import Color

    class FakeMoveLogger:
        def __init__(self):
            self.ticks = []
            self.player_names = {Color.WHITE: "White", Color.BLACK: "Black"}
            self.moves = {Color.WHITE: [], Color.BLACK: []}
            self.score = {Color.WHITE: 0, Color.BLACK: 0}

        def tick(self, ms):
            self.ticks.append(ms)

    move_logger = FakeMoveLogger()
    renderer = Renderer(move_logger)

    frame, layout = gui_app._render_frame(FakeManager(), bridge, controller, move_logger, renderer, 60)

    assert frame.shape == (layout.canvas_h, layout.canvas_w, 3)
    assert move_logger.ticks == [bridge.get_state().current_time]


def test_render_frame_non_game_state_draws_current_state_without_bridge():
    layout = make_layout(60)
    menu = MenuState(lambda: None, lambda: None, layout.canvas_w, layout.canvas_h)

    class FakeManager:
        current = menu

    frame, returned_layout = gui_app._render_frame(FakeManager(), None, None, None, None, 60)
    assert frame.shape == (returned_layout.canvas_h, returned_layout.canvas_w, 3)
    # MenuState.draw painted its buttons/title — background should not be uniform.
    assert frame.min() != frame.max()

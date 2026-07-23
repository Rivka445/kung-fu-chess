import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
from shared.model.board import Board
from shared.model.position import Position
from shared.model.piece import Color
from shared.model.game_state import GameState, PendingMove, AirbornePiece
from shared.constants.constants import DEFAULT_BOARD
from server.utils.board_parser import parse_row
from client.graphics.renderer import Renderer, make_layout
from client.graphics.panel_renderer import PanelRenderer


def _default_board():
    board = Board()
    for row in DEFAULT_BOARD:
        board.add_parsed_row(parse_row(row, board.expected_cols))
    return board


def test_make_layout_clamps_to_bounds():
    tiny = make_layout(1)
    assert tiny.cell_size == 40  # MIN_CELL_SIZE
    huge = make_layout(9999)
    assert huge.cell_size == 150  # MAX_CELL_SIZE


def test_make_layout_derives_canvas_geometry():
    layout = make_layout(100)
    assert layout.board_size == 800
    assert layout.canvas_w == 260 + 30 + 800 + 30 + 260
    assert layout.canvas_h == 30 + 800 + 30


def test_renderer_draws_default_board_without_selection():
    board = _default_board()
    state = GameState()
    canvas, layout = Renderer().draw(board, state, selected=None, cell_size=60)
    assert canvas.img.shape == (layout.canvas_h, layout.canvas_w, 4)


def test_renderer_draws_selection_and_legal_moves_overlay():
    board = _default_board()
    state = GameState()
    selected = Position(7, 0)  # white rook's starting square
    canvas, layout = Renderer().draw(board, state, selected=selected, cell_size=60)
    x = layout.board_x + selected.col * layout.cell_size
    y = layout.board_y + selected.row * layout.cell_size
    assert canvas.img[y + 5, x + 5][3] > 0


def test_renderer_draws_moving_piece_and_cooldown_overlay():
    board = _default_board()
    state = GameState(current_time=500)
    source = Position(6, 0)  # white pawn
    state.pending_moves.append(PendingMove(source, Position(4, 0), arrival=2000))
    state.cooldowns[Position(6, 1)] = 1500
    canvas, layout = Renderer().draw(board, state, selected=None, cell_size=60)
    assert canvas.img.shape == (layout.canvas_h, layout.canvas_w, 4)


def test_renderer_draws_airborne_piece():
    board = _default_board()
    state = GameState(current_time=200)
    pos = Position(6, 2)  # white pawn
    state.airborne.append(AirbornePiece(pos, landing_time=1000))
    canvas, layout = Renderer().draw(board, state, selected=None, cell_size=60)
    assert canvas.img.shape == (layout.canvas_h, layout.canvas_w, 4)


def test_renderer_draws_game_over_and_disconnect_banner():
    board = _default_board()
    state = GameState(game_over=True, disconnect_seconds_left=7)
    plain_state = GameState()
    canvas, layout = Renderer().draw(board, state, selected=None, cell_size=60)
    plain_canvas, _ = Renderer().draw(board, plain_state, selected=None, cell_size=60)
    assert canvas.img.shape == (layout.canvas_h, layout.canvas_w, 4)
    # "GAME OVER" text + disconnect banner paint extra pixels vs. the plain board.
    assert not np.array_equal(canvas.img, plain_canvas.img)


def test_panel_renderer_draws_player_header_and_move_rows():
    class FakeLogger:
        pass

    logger = FakeLogger()
    logger.player_names = {Color.WHITE: "Alice", Color.BLACK: "Bob"}
    logger.moves = {Color.WHITE: [("00:01", "e2e4")], Color.BLACK: []}
    logger.score = {Color.WHITE: 9, Color.BLACK: 0}

    panel = PanelRenderer(logger)
    layout = make_layout(60)
    bg = np.zeros((layout.canvas_h, layout.canvas_w, 4), dtype=np.uint8)
    panel.draw(bg, 0, Color.WHITE, layout)
    assert bg.any()

import numpy as np
from client.graphics.img import Img
from client.graphics.sprite import get_sprite_sheet, piece_state
from client.graphics.theme import COORD_SIZE, SIDEBAR_W
from core.model.board import Board
from core.model.game_state import GameState
from core.model.position import Position
from constants import MOVE_DURATION


def _pos_to_px(pos: Position, layout) -> tuple[int, int]:
    return layout.board_x + pos.col * layout.cell_size, layout.board_y + pos.row * layout.cell_size


def _interpolated_px(move, current_time: int, layout) -> tuple[int, int]:
    distance   = max(abs(move.target.row - move.source.row),
                     abs(move.target.col - move.source.col))
    start_time = move.arrival - distance * MOVE_DURATION
    t  = (current_time - start_time) / (move.arrival - start_time)
    t  = max(0.0, min(1.0, t))
    sx, sy = _pos_to_px(move.source, layout)
    tx, ty = _pos_to_px(move.target, layout)
    return int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)


def _state_start(pos, state_name: str, game_state: GameState) -> int:
    if state_name in ("short_rest", "long_rest"):
        return game_state.cooldowns.get(pos, 0) - MOVE_DURATION
    if state_name == "move":
        move = next((m for m in game_state.pending_moves if m.source == pos), None)
        if move:
            distance = max(abs(move.target.row - move.source.row),
                           abs(move.target.col - move.source.col))
            return move.arrival - MOVE_DURATION * distance
    return game_state.cooldowns.get(pos, 0)


def _draw_piece(canvas: Img, frame: Img, piece, x: int, y: int):
    frame.draw_on(canvas, x, y)


class PieceRenderer:
    def draw_all(self, canvas: Img, board: Board, state: GameState, layout):
        self._draw_stationary(canvas, board, state, layout)
        self._draw_moving(canvas, board, state, layout)
        self._draw_airborne(canvas, board, state, layout)

    def _draw_stationary(self, canvas: Img, board: Board, state: GameState, layout):
        moving_sources = {m.source for m in state.pending_moves}
        airborne_cells = {a.cell for a in state.airborne}
        for row in range(len(board.matrix)):
            for col in range(len(board.matrix[row])):
                pos   = Position(row, col)
                piece = board.get_piece(pos)
                if piece is None or pos in moving_sources or pos in airborne_cells:
                    continue
                sheet = get_sprite_sheet(piece)
                s     = piece_state(pos, state)
                frame = sheet.get_frame(s, state.current_time, _state_start(pos, s, state), layout.cell_size)
                x, y  = _pos_to_px(pos, layout)
                _draw_piece(canvas, frame, piece, x, y)
                self._draw_cooldown_overlay(canvas.img, pos, state, layout)

    def _draw_moving(self, canvas: Img, board: Board, state: GameState, layout):
        for move in state.pending_moves:
            piece = board.get_piece(move.source)
            if piece is None:
                continue
            distance = max(abs(move.target.row - move.source.row),
                           abs(move.target.col - move.source.col))
            frame = get_sprite_sheet(piece).get_frame("move", state.current_time,
                                                       move.arrival - MOVE_DURATION * distance,
                                                       layout.cell_size)
            x, y = _interpolated_px(move, state.current_time, layout)
            _draw_piece(canvas, frame, piece, x, y)

    def _draw_airborne(self, canvas: Img, board: Board, state: GameState, layout):
        for airborne in state.airborne:
            piece = board.get_piece(airborne.cell)
            if piece is None:
                continue
            frame = get_sprite_sheet(piece).get_frame("jump", state.current_time,
                                                       airborne.landing_time - MOVE_DURATION,
                                                       layout.cell_size)
            x, y = _pos_to_px(airborne.cell, layout)
            _draw_piece(canvas, frame, piece, x, y)

    def _draw_cooldown_overlay(self, bg, pos: Position, state: GameState, layout):
        cooldown_until = state.cooldowns.get(pos, 0)
        if cooldown_until <= state.current_time:
            return
        ratio = max(0.0, (cooldown_until - state.current_time) / MOVE_DURATION)
        x, y  = _pos_to_px(pos, layout)
        h = int(layout.cell_size * ratio)
        if h > 0:
            bg[y:y + h, x:x + layout.cell_size, :3] = (
                0.55 * bg[y:y + h, x:x + layout.cell_size, :3] + 0.45 * 40
            ).astype(np.uint8)

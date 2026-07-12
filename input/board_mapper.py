from model.position import Position


def pixel_to_pos(x: int, y: int, cell_size: int) -> Position:
    return Position(y // cell_size, x // cell_size)

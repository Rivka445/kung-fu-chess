from model.position import Position


def pixel_to_pos(x: int, y: int, cell_size: int) -> Position:
    """Convert pixel coordinates to a board Position by dividing by cell size."""
    return Position(y // cell_size, x // cell_size)

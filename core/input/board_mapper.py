from core.model.position import Position


def pixel_to_pos(x: int, y: int, cell_size: int,
                 offset_x: int = 0, offset_y: int = 0) -> Position:
    """Convert pixel coordinates to a board Position, accounting for board offset."""
    return Position((y - offset_y) // cell_size, (x - offset_x) // cell_size)

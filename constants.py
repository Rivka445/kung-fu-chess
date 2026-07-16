import pathlib

# The size of each board cell in pixels, used to convert pixel coordinates to board positions
CELL_SIZE     = 100
MIN_CELL_SIZE = 40
MAX_CELL_SIZE = 150
ZOOM_STEP     = 5    # pixels per +/- keypress

# The time in milliseconds it takes for a piece to travel from its source to its target
MOVE_DURATION = 1000

# Point value of each piece type (used for score calculation)
PIECE_POINTS = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}

IMAGES_DIR  = pathlib.Path(__file__).parent / "assets" / "assets" / "images"
PIECES_DIR  = pathlib.Path(__file__).parent / "pieces_classic" / "pieces_classic"
BOARD_IMAGE = IMAGES_DIR / "board.png"

from abc import ABC, abstractmethod
from models.position import from_chess_notation
from logger import logger

# Global registry that maps command names to their handler instances.
# Commands register themselves automatically using the @register decorator.
_REGISTRY = {}


class Command(ABC):
    """Base class for all game commands. Enforces a uniform execute interface."""
    @abstractmethod
    def execute(self, game, parts, cell_size): ...


def register(name):
    """Decorator that registers a command class under the given name in the global registry.
    When applied to a class, it instantiates the class and stores it so execute_command can look it up by name."""
    def decorator(cls):
        _REGISTRY[name] = cls()
        return cls
    return decorator


def _parse_square(token, board_rows, cell_size):
    """Converts a chess notation token such as 'e4' into pixel coordinates (x, y).
    Used to support chess notation as an alternative to raw pixel input in commands."""
    pos = from_chess_notation(token, board_rows)
    return pos.col * cell_size + cell_size // 2, pos.row * cell_size + cell_size // 2


@register("click")
class ClickCommand(Command):
    """Handles the 'click' command, which selects a piece or moves a selected piece to a target.
    Accepts either pixel coordinates ('click 50 50') or chess notation ('click e2 e4')."""
    def execute(self, game, parts, cell_size):
        if len(parts) != 3:
            return
        board_rows = len(game.board.matrix)
        try:
            x, y = int(parts[1]), int(parts[2])
            game.handle_click(x, y, cell_size)
        except ValueError:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
                x2, y2 = _parse_square(parts[2], board_rows, cell_size)
                game.handle_click(x, y, cell_size)
                game.handle_click(x2, y2, cell_size)
            except (IndexError, ValueError):
                logger.warning("invalid chess notation in click command: %s %s", parts[1], parts[2])


@register("wait")
class WaitCommand(Command):
    """Handles the 'wait' command, which advances the game clock by a given number of milliseconds.
    Example: 'wait 1000' advances time by one second and processes all moves that arrive in that window."""
    def execute(self, game, parts, cell_size):
        if len(parts) != 2:
            return
        try:
            game.handle_wait(int(parts[1]))
        except ValueError:
            logger.warning("invalid wait argument: %s", parts[1])


@register("jump")
class JumpCommand(Command):
    """Handles the 'jump' command, which launches a piece into the air from the given position.
    Accepts either pixel coordinates ('jump 150 150') or chess notation ('jump e4')."""
    def execute(self, game, parts, cell_size):
        board_rows = len(game.board.matrix)
        if len(parts) == 2:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
            except (IndexError, ValueError):
                logger.warning("invalid chess notation in jump command: %s", parts[1])
                return
        elif len(parts) == 3:
            try:
                x, y = int(parts[1]), int(parts[2])
            except ValueError:
                logger.warning("invalid jump arguments: %s %s", parts[1], parts[2])
                return
        else:
            return
        game.handle_jump(x, y, cell_size)


@register("print")
class PrintCommand(Command):
    """Handles the 'print board' command, which outputs the current board state to stdout with chess notation labels."""
    def execute(self, game, parts, cell_size):
        if len(parts) == 2 and parts[1] == "board":
            game.handle_print_board()


def execute_command(line, game, cell_size):
    """Parses a single command line and dispatches it to the appropriate registered command handler.
    If the command name is not found in the registry, the line is silently ignored."""
    parts = line.split()
    if not parts:
        return
    command = _REGISTRY.get(parts[0])
    if command:
        command.execute(game, parts, cell_size)
    else:
        logger.warning("unknown command: '%s'", parts[0])

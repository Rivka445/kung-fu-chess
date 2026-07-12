from abc import ABC, abstractmethod
from model.position import from_chess_notation
from board_io.board_printer import print_board
from logger import logger

_REGISTRY = {}


class Command(ABC):
    @abstractmethod
    def execute(self, controller, engine, parts, cell_size): ...


def register(name):
    def decorator(cls):
        _REGISTRY[name] = cls()
        return cls
    return decorator


def _parse_square(token, board_rows, cell_size):
    pos = from_chess_notation(token, board_rows)
    return pos.col * cell_size + cell_size // 2, pos.row * cell_size + cell_size // 2


@register("click")
class ClickCommand(Command):
    def execute(self, controller, engine, parts, cell_size):
        if len(parts) != 3:
            return
        board_rows = len(engine.board.matrix)
        try:
            controller.click(int(parts[1]), int(parts[2]), cell_size)
        except ValueError:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
                x2, y2 = _parse_square(parts[2], board_rows, cell_size)
                controller.click(x, y, cell_size)
                controller.click(x2, y2, cell_size)
            except (IndexError, ValueError):
                logger.warning("invalid chess notation in click: %s %s", parts[1], parts[2])


@register("wait")
class WaitCommand(Command):
    def execute(self, controller, engine, parts, cell_size):
        if len(parts) != 2:
            return
        try:
            engine.advance_time(int(parts[1]))
        except ValueError:
            logger.warning("invalid wait argument: %s", parts[1])


@register("jump")
class JumpCommand(Command):
    def execute(self, controller, engine, parts, cell_size):
        board_rows = len(engine.board.matrix)
        if len(parts) == 2:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
            except (IndexError, ValueError):
                logger.warning("invalid chess notation in jump: %s", parts[1])
                return
        elif len(parts) == 3:
            try:
                x, y = int(parts[1]), int(parts[2])
            except ValueError:
                logger.warning("invalid jump arguments: %s %s", parts[1], parts[2])
                return
        else:
            return
        controller.jump(x, y, cell_size)


@register("print")
class PrintCommand(Command):
    def execute(self, controller, engine, parts, cell_size):
        if len(parts) == 2 and parts[1] == "board":
            print_board(engine.board)


def execute(line: str, controller, engine, cell_size: int):
    parts = line.split()
    if not parts:
        return
    command = _REGISTRY.get(parts[0])
    if command:
        command.execute(controller, engine, parts, cell_size)
    else:
        logger.warning("unknown command: '%s'", parts[0])

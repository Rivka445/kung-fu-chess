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



@register("click")
class ClickCommand(Command):
    def execute(self, controller, engine, parts, cell_size):
        if len(parts) != 3:
            return
        board_rows = len(engine.board.matrix)
        try:
            source = from_chess_notation(parts[1], board_rows)
            target = from_chess_notation(parts[2], board_rows)
            controller.click_pos(source)
            controller.click_pos(target)
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
        if len(parts) != 2:
            return
        board_rows = len(engine.board.matrix)
        try:
            pos = from_chess_notation(parts[1], board_rows)
            controller.jump_pos(pos)
        except (IndexError, ValueError):
            logger.warning("invalid chess notation in jump: %s", parts[1])


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

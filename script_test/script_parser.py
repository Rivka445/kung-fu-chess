from abc import ABC, abstractmethod
from model.position import from_chess_notation
from board_io.board_printer import print_board
from constants import CELL_SIZE
from logger import logger

_REGISTRY = {}


class Command(ABC):
    @abstractmethod
    def execute(self, controller, engine, parts): ...


def register(name):
    def decorator(cls):
        _REGISTRY[name] = cls()
        return cls
    return decorator



@register("click")
class ClickCommand(Command):
    def execute(self, controller, engine, parts):
        if len(parts) != 3:
            return
        board_rows = len(engine.board.matrix)
        try:
            # Try pixel coordinates first (e.g. 50 150)
            controller.click(int(parts[1]), int(parts[2]), CELL_SIZE)
        except ValueError:
            try:
                # Fall back to chess notation (e.g. e2 e4)
                source = from_chess_notation(parts[1], board_rows)
                target = from_chess_notation(parts[2], board_rows)
                controller.click_pos(source)
                controller.click_pos(target)
            except (IndexError, ValueError):
                logger.warning("invalid click arguments: %s %s", parts[1], parts[2])


@register("wait")
class WaitCommand(Command):
    def execute(self, controller, engine, parts):
        if len(parts) != 2:
            return
        try:
            engine.advance_time(int(parts[1]))
        except ValueError:
            logger.warning("invalid wait argument: %s", parts[1])


@register("jump")
class JumpCommand(Command):
    def execute(self, controller, engine, parts):
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
    def execute(self, controller, engine, parts):
        if len(parts) == 2 and parts[1] == "board":
            print_board(engine.board)


def execute(line: str, controller, engine):
    parts = line.split()
    if not parts:
        return
    command = _REGISTRY.get(parts[0])
    if command:
        command.execute(controller, engine, parts)
    else:
        logger.warning("unknown command: '%s'", parts[0])

from models.position import from_chess_notation

_REGISTRY = {}


def register(name):
    def decorator(cls):
        _REGISTRY[name] = cls()
        return cls
    return decorator


def _parse_square(token, board_rows, cell_size):
    pos = from_chess_notation(token, board_rows)
    return pos.col * cell_size + cell_size // 2, pos.row * cell_size + cell_size // 2


@register("click")
class ClickCommand:
    def execute(self, game, parts, cell_size):
        if len(parts) != 3:
            return
        board_rows = len(game.board.matrix)
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
                x2, y2 = _parse_square(parts[2], board_rows, cell_size)
                game.handle_click(x, y, cell_size)
                game.handle_click(x2, y2, cell_size)
                return
            except (IndexError, ValueError):
                return
        game.handle_click(x, y, cell_size)


@register("wait")
class WaitCommand:
    def execute(self, game, parts, cell_size):
        if len(parts) != 2:
            return
        try:
            game.handle_wait(int(parts[1]))
        except ValueError:
            return


@register("jump")
class JumpCommand:
    def execute(self, game, parts, cell_size):
        board_rows = len(game.board.matrix)
        if len(parts) == 2:
            try:
                x, y = _parse_square(parts[1], board_rows, cell_size)
            except (IndexError, ValueError):
                return
        elif len(parts) == 3:
            try:
                x, y = int(parts[1]), int(parts[2])
            except ValueError:
                return
        else:
            return
        game.handle_jump(x, y, cell_size)


@register("print")
class PrintCommand:
    def execute(self, game, parts, cell_size):
        if len(parts) == 2 and parts[1] == "board":
            game.handle_print_board()


def execute_command(line, game, cell_size):
    parts = line.split()
    if not parts:
        return
    command = _REGISTRY.get(parts[0])
    if command:
        command.execute(game, parts, cell_size)


def execute_command(line, game, cell_size):
    parts = line.split()

    if len(parts) == 0:
        return

    if parts[0] == "click" and len(parts) == 3:
        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            return
        game.handle_click(x, y, cell_size)

    elif parts[0] == "wait" and len(parts) == 2:
        try:
            ms = int(parts[1])
        except ValueError:
            return
        game.handle_wait(ms)

    elif parts[0] == "jump" and len(parts) == 3:
        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            return
        game.handle_jump(x, y, cell_size)

    elif len(parts) == 2 and parts[0] == "print" and parts[1] == "board":
        game.handle_print_board()
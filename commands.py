
def execute_command(line, game, cell_size):
    parts = line.split()

    if len(parts) == 0:
        return

    if parts[0] == "click" and len(parts) == 3:
        x = int(parts[1])
        y = int(parts[2])
        game.handle_click(x, y, cell_size)

    elif parts[0] == "wait" and len(parts) == 2:
        ms = int(parts[1])
        game.handle_wait(ms)

    elif len(parts) == 2 and parts[0] == "print" and parts[1] == "board":
        game.handle_print_board()
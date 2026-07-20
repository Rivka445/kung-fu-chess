"""Single-process lobby: collects 2 player usernames from the shell."""


def run_lobby() -> tuple[str, str]:
    """
    Block until 2 players have entered their usernames.
    Returns (white_name, black_name).
    """
    print("=== Kung-Fu Chess Lobby ===")
    white = input("Player 1, enter your username (White): ").strip() or "White"
    black = input("Player 2, enter your username (Black): ").strip() or "Black"
    print(f"\n{white} (White) vs {black} (Black) — starting game...\n")
    return white, black

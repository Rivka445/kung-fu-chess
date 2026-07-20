import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    if "--gui" in sys.argv:
        from ui.graphics.gui_app import run
        use_ws = "--ws" in sys.argv
        if use_ws:
            # WS mode: username entered in shell, server assigns color
            username = input("Enter your username: ").strip() or "Player"
            run(use_ws=True, white_name=username, black_name=username)
        else:
            # Local mode: two players on same machine
            from server.lobby import run_lobby
            white_name, black_name = run_lobby()
            run(use_ws=False, white_name=white_name, black_name=black_name)
    else:
        from script_test.script_runner import run
        run()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    if "--gui" in sys.argv:
        from ui.graphics.gui_app import run
        run()
    else:
        from script_test.script_runner import run
        run()

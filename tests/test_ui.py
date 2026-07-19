import pytest
import numpy as np
from ui.state.state_manager import StateManager
from ui.state.base import UIState
from ui.components.button import Button
from ui.components.label import Label
from ui.state.menu_state import MenuState
from ui.state.game_over_state import GameOverState

class MockState(UIState):
    def __init__(self):
        self.entered = False
        self.exited = False
        self.last_event = None
        self.last_ms = 0

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def handle_input(self, event: dict) -> None:
        self.last_event = event

    def update(self, ms: int) -> None:
        self.last_ms = ms


def test_state_manager():
    initial = MockState()
    manager = StateManager(initial)
    assert initial.entered
    assert not initial.exited

    # Test delegation
    manager.handle_input({"type": "click"})
    assert initial.last_event == {"type": "click"}

    manager.update(100)
    assert initial.last_ms == 100

    # Test transition
    new_state = MockState()
    manager.transition(new_state)
    assert initial.exited
    assert new_state.entered


def test_button_click():
    btn = Button(10, 20, 100, 50, "Test")
    assert btn.is_clicked(15, 25)
    assert btn.is_clicked(10, 20)
    assert btn.is_clicked(110, 70)
    assert not btn.is_clicked(5, 25)
    assert not btn.is_clicked(15, 15)
    assert not btn.is_clicked(115, 75)


def test_label_init():
    lbl = Label(10, 20, "Hello")
    assert lbl.x == 10
    assert lbl.y == 20
    assert lbl.text == "Hello"


def test_menu_state_clicks():
    started = False
    quitted = False

    def on_start():
        nonlocal started
        started = True

    def on_quit():
        nonlocal quitted
        quitted = True

    state = MenuState(on_start, on_quit, 800, 600)
    
    # Click start button (cx - 80, cy - 20) -> (320, 280)
    # Button is at x=320, y=280, w=160, h=45
    state.handle_input({"type": "click", "x": 350, "y": 290})
    assert started
    assert not quitted

    # Click quit button (cx - 80, cy + 45) -> (320, 345)
    # Button is at x=320, y=345, w=160, h=45
    state.handle_input({"type": "click", "x": 350, "y": 350})
    assert quitted


def test_game_over_state_clicks():
    restarted = False
    quitted = False

    def on_restart():
        nonlocal restarted
        restarted = True

    def on_quit():
        nonlocal quitted
        quitted = True

    state = GameOverState(on_restart, on_quit, 800, 600)
    
    # Click play again button (cx - 80, cy) -> (320, 300)
    # Button is at x=320, y=300, w=160, h=45
    state.handle_input({"type": "click", "x": 350, "y": 310})
    assert restarted
    assert not quitted

    # Click quit button (cx - 80, cy + 65) -> (320, 365)
    # Button is at x=320, y=365, w=160, h=45
    state.handle_input({"type": "click", "x": 350, "y": 370})
    assert quitted


def test_ui_container():
    from ui.components.container import UIContainer
    container = UIContainer()
    btn = Button(10, 20, 100, 50, "Test")
    lbl = Label(10, 20, "Hello")

    container.add(btn)
    container.add(lbl)
    assert len(container._components) == 2

    container.remove(btn)
    assert len(container._components) == 1
    assert container._components[0] == lbl

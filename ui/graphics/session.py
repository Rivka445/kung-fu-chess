from core.events.event_bus import EventBus, GameStarted, GameOver
from core.events.move_logger import MoveLogger
from ui.sound.sound_manager import SoundManager
from ui.engine_bridge.ws_bridge import WebSocketBridge
from ui.input.controller import Controller
from core.model.piece import Color


class _GameOverWatch:
    """
    Bus-driven game-over flag, replacing per-frame polling of bridge state.
    In WS mode the GameOver event may arrive on the WebSocketBridge's
    background recv thread, so this only ever sets a flag here — the actual
    state-machine transition still happens on the main render loop thread.
    """
    def __init__(self, bus: EventBus):
        self.game_over = False
        bus.subscribe(GameOver, lambda e: setattr(self, "game_over", True))


class _MatchFoundWatch:
    """
    Bus-driven "matched" flag, mirroring _GameOverWatch. GameStarted is
    published by the server once matchmaking pairs two players, and arrives
    on the WebSocketBridge's background recv thread — this just sets a flag
    for the main render loop to notice and transition out of SearchingState.
    """
    def __init__(self, bus: EventBus):
        self.matched = False
        bus.subscribe(GameStarted, lambda e: setattr(self, "matched", True))


def build_bridge(username: str = "Player") -> tuple:
    """
    The server owns the real GameEngine/RuleEngine — this process never builds
    one. It only mirrors the state the server sends and renders it, via a plain
    EventBus for local listeners (sound, move log) to subscribe to.

    Only login happens here — matchmaking is deferred until the player clicks
    Play (SearchingState calls bridge.start_search()). Player names aren't known
    until a match is found, so move_logger is built later too (see
    build_move_logger_for_match), once GameStarted fires.
    """
    bus = EventBus()
    bridge = WebSocketBridge(bus, username=username)
    bridge.login()
    move_logger = None
    SoundManager(bus)
    game_over_watch = _GameOverWatch(bus)
    match_found_watch = _MatchFoundWatch(bus)
    controller = Controller(bridge)
    return bridge, controller, move_logger, game_over_watch, match_found_watch, bus


def build_move_logger_for_match(bridge: WebSocketBridge, bus: EventBus, my_name: str) -> MoveLogger:
    """Build the MoveLogger once a WS match is found and player names/colors are known."""
    server_white, server_black = bridge.player_names[Color.WHITE], bridge.player_names[Color.BLACK]
    return MoveLogger(bridge.get_board(), bus,
                      white_name=server_white + (" (You)" if server_white == my_name else ""),
                      black_name=server_black + (" (You)" if server_black == my_name else ""))

# Kung-Fu Chess

A real-time chess engine where pieces move simultaneously — no turns, no waiting.
Players submit moves at any time, and pieces travel to their destination over a fixed duration.

---

## How It Works

- A piece takes `MOVE_DURATION` ms to travel from source to target (scaled by distance).
- After arriving, a piece enters a **cooldown** period before it can move again.
- Pieces can be **launched** into the air, landing after `MOVE_DURATION` ms.
- Collisions between pieces are resolved automatically.

---

## Project Structure

```
chess-project/
├── model/               # Core domain — board, pieces, positions, game state
├── rules/               # Chess move legality
├── real_time/           # Real-time execution and collision resolution
├── engine/              # Game assembly — GameEngine facade + GameBuilder
├── events/              # Observer Pattern — game event notifications
├── input/               # Player input — click handling and board mapping
├── graphics/            # UI layer — rendering, sprites, GUI loop
│   ├── gui_app.py       # Main game loop (OpenCV window, mouse, ~60 fps)
│   ├── renderer.py      # Draws board, pieces, panels, selection highlight
│   ├── sprite.py        # SpriteSheet — animated frames per piece state
│   └── img.py           # Img wrapper — load, draw, blend images
├── board_io/            # Board parsing and printing
├── script_test/         # Script-based simulation runner
├── tests/               # Unit and integration tests
└── constants.py         # CELL_SIZE, MOVE_DURATION
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│         graphics (Renderer, GUIApp)     │  ← UI — renders board & pieces at ~60fps
├─────────────────────────────────────────┤
│           script_test / input           │  ← Player input & script commands
├─────────────────────────────────────────┤
│              GameEngine                 │  ← Central facade
├──────────────────┬──────────────────────┤
│   RuleEngine     │   RealTimeArbiter    │  ← Chess rules / Real-time execution
├──────────────────┼──────────────────────┤
│   piece_rules    │  CollisionResolver   │  ← Per-piece strategies / Collision logic
├──────────────────┴──────────────────────┤
│         model (Board, GameState)        │  ← Pure domain — no logic
└─────────────────────────────────────────┘
                     ↓
              events (listeners)
```

**Key principle:** each layer has a single responsibility and depends only on layers below it.

---

## Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| Strategy | `piece_rules.py` | Each piece type has its own movement strategy — no `if/elif` on piece type |
| Strategy | `piece_status.py` | Each status defines its own `can_act()` behavior |
| Observer | `events/` | Listeners react to game events without coupling to the engine |
| Facade | `GameEngine`, `RuleEngine` | Simple interfaces hiding internal complexity |
| Builder | `GameBuilder` | Fluent API for constructing a game row by row |
| Command | `script_parser.py` | Each script command is an encapsulated object registered by name |
| Cache | `sprite.py` | `SpriteSheet` instances are cached by piece type — no disk reads per frame |

---

## GameEngine API

| Method | Description |
|--------|-------------|
| `request_move(source, target)` | Submit a move — rejected if piece is busy or move is illegal |
| `request_jump(pos)` | Launch the piece at `pos` into the air |
| `advance_time(ms)` | Advance the game clock by `ms` milliseconds |
| `add_listener(listener)` | Register a `GameEventListener` to receive game events |

### GameEventListener hooks

| Method | Fired when |
|--------|-----------|
| `on_move_applied(source, target)` | A piece successfully moves |
| `on_king_captured(pos)` | A king is captured — game over |
| `on_pawn_promoted(pos)` | A pawn reaches the last row |
| `on_collision(pos)` | A collision removes one or more pieces |

---

## Script Commands

A game script has two sections: `Board:` and `Commands:`.

```
Board:
rnbqkbnr
pppppppp
........
........
........
........
PPPPPPPP
RNBQKBNR

Commands:
click e2 e4
wait 1000
click e7 e5
wait 1000
print board
```

| Command | Description |
|---------|-------------|
| `click <sq1> <sq2>` | Move piece from sq1 to sq2 (chess notation) |
| `wait <ms>` | Advance the game clock by the given milliseconds |
| `jump <sq>` | Launch the piece at the given square into the air |
| `print board` | Print the current board state to stdout |

---

## Running the GUI

```bash
python main.py
```

| Control | Action |
|---------|--------|
| Left click a piece | Select it |
| Left click a target square | Move the selected piece |
| Right click a piece | Launch it into the air (jump) |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| Resize window | Board scales automatically |
| `Q` or `ESC` | Quit |

---

## Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `MOVE_DURATION` | `1000` ms | Time for a piece to travel one square |
| `CELL_SIZE` | `100` px | Pixel size of each board cell |

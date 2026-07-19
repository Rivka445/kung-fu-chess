# 02 — Engine, Rules, Real-Time, Input, Events & Script

---

## core/rules/piece_rules.py
**Design Pattern: Strategy**

כל סוג כלי מקבל אסטרטגיית תנועה משלו — אין `if/elif` על סוג הכלי.

### `MoveStrategy` (ABC)
| מתודה | תיאור |
|---|---|
| `is_legal(piece, source, target, board)` | האם המהלך חוקי |
| `_available(piece, target, board)` | helper — target ריק או אויב |
| `_clear(source, target, board)` | helper — אין חוסמים בדרך |

### אסטרטגיות קונקרטיות

| מחלקה | חוק תנועה |
|---|---|
| `KingStrategy` | צעד אחד בכל כיוון (`dr<=1, dc<=1`) |
| `RookStrategy` | קו ישר (dr==0 או dc==0), נתיב פנוי |
| `BishopStrategy` | אלכסון (`dr==dc`), נתיב פנוי |
| `QueenStrategy` | רץ + פיל, נתיב פנוי |
| `KnightStrategy` | L-shape `(2,1)` או `(1,2)`, קופץ מעל כלים |
| `PawnStrategy` | קדימה 1, קדימה 2 מהשורה ההתחלתית, לכידה אלכסונית |

**`PawnStrategy` בפירוט:**
- `dc==0, dr==direction` → קדימה 1, target חייב להיות ריק
- `dc==0, dr==2*direction` מהשורה ההתחלתית → קדימה 2, שני תאים ריקים
- `abs(dc)==1, dr==direction` → לכידה אלכסונית, חייב להיות אויב ב-target
- `direction = -1` ללבן (שורות יורדות), `+1` לשחור

### `MOVE_STRATEGIES` (dict)
`PieceType → MoveStrategy` — רישום כל האסטרטגיות. נוצר פעם אחת.

---

## core/rules/rule_engine.py
**Design Pattern: Facade**

### `RuleEngine`
ממשק פשוט לבדיקת חוקיות מהלך. מסתיר את מנגנון האסטרטגיות.

### `is_legal(piece, source, target, board)` → `bool`
בדיקות בסדר:
1. piece לא None
2. target בתוך הלוח
3. source ≠ target
4. האסטרטגיה הספציפית לסוג הכלי מאשרת

---

## core/real_time/collision_resolver.py

### פונקציות עזר
- `_group_by_target(moves)` → dict `(arrival, target) → list[PendingMove]` — O(M)
- `_edge_key(move)` → tuple סימטרי — A→B ו-B→A מייצרים אותו מפתח

### `CollisionResolver`
מזהה ופותר שני סוגי התנגשויות. **לא נוגע בלוח** — רק מסנן מהלכים.

#### `resolve_head_on(ready)` → `list[PendingMove]`
מסיר את המהלך המאוחר יותר מכל זוג head-on (A→B ו-B→A באותו זמן).
- מקבץ לפי `_edge_key`
- בזוג אמיתי: `pair[0].source == pair[1].target`
- המפסיד: זה עם `seq` גבוה יותר (הוגש מאוחר יותר)

#### `find_simultaneous(ready)` → `set[Position]`
מחזיר קבוצת target squares שאליהם מגיעים שני כלים או יותר בו-זמנית.

---

## core/real_time/real_time_arbiter.py

### `RealTimeArbiter`
מנוע הזמן האמת. מקבל `board` ו-`listeners` בבנייה.

#### `_partition(state)` → `(ready, landed)`
מפריד מהלכים ו-airborne ל"מוכנים" ו"עדיין ממתינים". מעדכן את state in-place.

#### `_apply(move, simultaneous, landed, state)`
מחיל מהלך בודד. סדר עדיפויות:

| מקרה | תנאי | פעולה |
|---|---|---|
| 1. Simultaneous | `move.target in simultaneous` | מסיר את הכלי ב-target, קורא `on_collision` |
| 2. Airborne collision | כלי אויב נוחת על אותו target | מסיר את source piece, קורא `on_collision` |
| 3. Friendly block | כלי ידידותי ב-target | לא עושה כלום |
| 4. Normal move | כל שאר המקרים | מזיז כלי, מעדכן cooldown, קורא `on_move_applied` |

אחרי מהלך רגיל בודק:
- האם נלכד מלך → `on_king_captured`, `state.game_over = True`
- האם רגלי הגיע לשורה אחרונה → `promote_pawn`, `on_pawn_promoted`

**חישוב cooldown:** `cooldowns[target] = arrival + MOVE_DURATION`

#### `advance(ms, state)`
מקדם את שעון המשחק. הזרימה:
1. `state.current_time += ms`
2. `cleanup_cooldowns()`
3. `_partition` — מפריד מוכנים
4. מעדכן cooldowns לנוחתים
5. `resolve_head_on` — מסיר head-on collisions
6. מקבץ לפי arrival time ומחיל בסדר כרונולוגי

#### `launch(pos, state)`
מוסיף `AirbornePiece` ל-`state.airborne` עם `landing_time = current_time + MOVE_DURATION`.

---

## core/engine/game_engine.py
**Design Pattern: Facade**

### `GameEngine`
הממשק המרכזי לכל הפרויקט. מחבר board, rules, arbiter, ו-listeners.

| שדה | תיאור |
|---|---|
| `board` | ה-Board |
| `rules` | ה-RuleEngine |
| `state` | ה-GameState |
| `_listeners` | רשימת GameEventListener |
| `_arbiter` | ה-RealTimeArbiter |

#### `add_listener(listener)`
מוסיף listener לרשימה.

#### `request_move(source, target)`
מגיש בקשת מהלך. נדחית אם:
- המשחק הסתיים
- אין כלי ב-source
- הכלי עסוק (in-flight/cooldown)
- המהלך לא חוקי לפי RuleEngine

אם עובר: מחשב `arrival = current_time + MOVE_DURATION * chebyshev_distance` ומוסיף `PendingMove`.

**Chebyshev distance:** `max(|dr|, |dc|)` — כך כלי שזז 3 תאים לוקח 3x MOVE_DURATION.

#### `request_jump(pos)`
מפעיל `_arbiter.launch()` אם הכלי קיים ולא עסוק.

#### `advance_time(ms)`
מעביר ל-`_arbiter.advance()`.

---

## core/engine/game_builder.py
**Design Pattern: Builder**

### `GameApplication` (dataclass, frozen=True)
| שדה | תיאור |
|---|---|
| `engine` | GameEngine |
| `controller` | Controller |

### `build_game(board, listeners)` → `GameApplication`
פונקציית factory — מחברת engine + RuleEngine + controller + listeners.

### `GameBuilder`
Builder fluent API לבנייה שורה-שורה מסקריפט.

| מתודה | תיאור |
|---|---|
| `with_row(line)` | מפרסר שורה ומוסיף ללוח, מחזיר `self` |
| `with_listener(listener)` | מוסיף listener, מחזיר `self` |
| `build()` | קורא ל-`build_game` ומחזיר `GameApplication` |

---

## core/input/board_mapper.py

### `pixel_to_pos(x, y, cell_size, offset_x, offset_y)` → `Position`
ממיר קואורדינטות פיקסל למיקום על הלוח.
- `row = (y - offset_y) // cell_size`
- `col = (x - offset_x) // cell_size`

---

## core/input/controller.py

### `Controller`
מתרגם קלט שחקן לפעולות על ה-engine.

| שדה | תיאור |
|---|---|
| `_engine` | GameEngine |
| `_selected` | `Position | None` — הריבוע שנבחר בלחיצה ראשונה |

#### `click(x, y, cell_size, offset_x, offset_y)`
ממיר פיקסלים ל-Position וקורא ל-`click_pos`.

#### `click_pos(pos)`
לוגיקת בחירה ומהלך:
- לחיצה ראשונה על כלי → שומר ב-`_selected`
- לחיצה שנייה על כלי ידידותי → re-select
- לחיצה שנייה על ריק/אויב → `request_move(_selected, pos)`, מנקה `_selected`

#### `jump(x, y, ...)` / `jump_pos(pos)`
קורא ל-`engine.request_jump`.

---

## core/events/base.py
**Design Pattern: Observer**

### `GameEventListener` (ABC)
ממשק ה-Observer. כל המתודות הן no-op כברירת מחדל — ניתן לממש רק חלק.

| מתודה | מתי נקראת |
|---|---|
| `on_move_applied(source, target)` | כלי הגיע ליעד בהצלחה |
| `on_capture(captured_piece, capturing_color)` | לפני עדכון הלוח בלכידה |
| `on_king_captured(pos)` | מלך נלכד — סוף משחק |
| `on_pawn_promoted(pos)` | רגלי הגיע לשורה אחרונה |
| `on_collision(pos)` | התנגשות הסירה כלי/ים |

---

## core/events/log_listener.py

### `LogListener(GameEventListener)`
Observer קונקרטי שמלוגג כל אירוע.
- `on_move_applied` → `logger.info`
- `on_king_captured` → `logger.warning`
- `on_pawn_promoted` → `logger.info`
- `on_collision` → `logger.info`

---

## core/events/move_logger.py

### `MoveLogger(GameEventListener)`
עוקב אחר מהלכים וניקוד לכל צבע. משמש ל-UI (פאנל צד).

| שדה | תיאור |
|---|---|
| `player_names` | dict Color → שם שחקן |
| `moves` | dict Color → list of `(time_str, move_str)` |
| `score` | dict Color → int |
| `_current_time` | זמן נוכחי (מתעדכן ע"י `tick`) |

**מתודות:**
- `tick(current_time)` — מעדכן את הזמן הנוכחי (נקרא כל פריים)
- `on_capture(captured_piece, capturing_color)` — מוסיף נקודות לפי `PIECE_POINTS`
- `on_move_applied(source, target)` — מוסיף רשומה ל-`moves` עם timestamp
- `_sq(pos)` — helper: Position → `"e2"` וכד'
- `_fmt_time(ms)` — helper: ms → `"00:04.105"`

---

## script_test/script_parser.py
**Design Pattern: Command**

כל פקודת סקריפט היא אובייקט Command נפרד הרשום ב-registry.

### `Command` (ABC)
- `execute(controller, engine, parts)` — מבצע את הפקודה

### `_REGISTRY` (dict)
`name → Command instance` — נבנה ע"י decorator `@register`.

### `@register(name)` decorator
רושם מחלקה ב-`_REGISTRY` בזמן הגדרתה.

### פקודות רשומות

| פקודה | מחלקה | תיאור |
|---|---|---|
| `click sq1 sq2` | `ClickCommand` | מהלך בסימון שחמט או פיקסלים |
| `wait ms` | `WaitCommand` | מקדם את שעון המשחק |
| `jump sq` | `JumpCommand` | קפיצה לאוויר |
| `print board` | `PrintCommand` | מדפיס את הלוח ל-stdout |

### `execute(line, controller, engine)`
מפצל שורה, מחפש ב-`_REGISTRY`, מפעיל. אם לא נמצא → `logger.warning`.

---

## script_test/script_runner.py

### `run(stream=None)`
מריץ סקריפט מ-stdin (או stream נתון).

**זרימה:**
1. קורא שורה-שורה
2. `Board:` → מתחיל לבנות לוח עם `GameBuilder`
3. `Commands:` → קורא `builder.build()`, עובר למצב פקודות
4. שורות לוח → `builder.with_row()`
5. שורות פקודות → `execute(line, controller, engine)`
6. שגיאת פרסור → מדפיס `ERROR <CODE>` ויוצא

---

## main.py / app.py

### `main.py`
נקודת כניסה ראשית.
- `--gui` → `ui.graphics.gui_app.run()`
- ללא דגל → `script_test.script_runner.run()`

### `app.py`
נקודת כניסה חלופית — מריץ ישירות את `script_runner.run()`.

# Kung-Fu Chess — Design Summary

## מה הפרויקט עושה
שחמט בזמן אמת — אין תורות. כל כלי נע במשך `MOVE_DURATION=1000ms`, אחרי הגעה נכנס ל-cooldown. שחקן יכול לשלוח מהלך בכל רגע.

---

## שכבות (מלמטה למעלה)

```
core/model      — נתונים טהורים, אין לוגיקה
core/rules      — חוקי שחמט
core/real_time  — ביצוע בזמן אמת + התנגשויות
core/engine     — Facade מרכזי (GameEngine)
core/input      — תרגום קלט → engine
core/events     — Observer notifications
client/             — רנדור + מסכים + bridge
```

כל שכבה תלויה רק בשכבות מתחתיה.

---

## Design Patterns

### Strategy — `piece_rules.py` + `piece_status.py`
- כל סוג כלי (King/Rook/...) הוא `MoveStrategy` נפרד ב-`MOVE_STRATEGIES` dict — אין `if/elif` על סוג הכלי
- כל סטטוס (Idle/InFlight/OnCooldown) מגדיר `can_act()` ו-`sprite_state()` בעצמו

### Observer — `core/events/`
- `GameEventListener` (ABC) עם hooks: `on_move_applied`, `on_king_captured`, `on_pawn_promoted`, `on_collision`
- `RealTimeArbiter` מודיע לכל ה-listeners בלי לדעת מי הם
- Implementations: `LogListener` (לוגינג), `MoveLogger` (ניקוד + היסטוריה ל-UI)

### Facade — `GameEngine` + `RuleEngine`
- `GameEngine` הוא הממשק היחיד לעולם החוץ: `request_move`, `request_jump`, `advance_time`, `add_listener`
- `RuleEngine` מסתיר את מנגנון ה-Strategy מאחוריו

### Builder — `GameBuilder`
- Fluent API: `GameBuilder().with_row(...).with_listener(...).build()`
- מחזיר `GameApplication(engine, controller)`

### Bridge — `client/engine_bridge/`
- `EngineBridge` (ABC) מנתק את ה-UI מה-engine
- `LocalBridge` — מימוש מקומי ישיר ל-`GameEngine`
- `WebSocketBridge` — מימוש מרוחק מול השרת דרך WebSocket

### State — `client/state/`
- `UIState` (ABC): `on_enter`, `on_exit`, `handle_input`, `update`
- `StateManager` מנהל מעברים בין: `MenuState` → `GameUIState` → `GameOverState`
- המעבר ל-GameOver מזוהה ב-`gui_app.py` כשמגלים `bridge.get_state().game_over == True`

### Composite — `client/components/`
- `UIComponent` (ABC) עם `draw(canvas)`
- `UIContainer` מחזיק רשימת `UIComponent` ומצייר את כולם — `MenuState` ו-`GameOverState` משתמשים בו

### Command — `script_test/script_parser.py`
- כל פקודת סקריפט (`click`, `wait`, `jump`, `print`) היא מחלקת `Command` נפרדת
- `@register("name")` decorator רושם אוטומטית ל-`_REGISTRY`

### Cache — `client/graphics/sprite.py`
- `get_sprite_sheet(piece)` מחזיר מ-`_cache` dict — טעינה מהדיסק פעם אחת בלבד

---

## זרימת מהלך מלאה

```
שחקן לוחץ
    → Controller.click_pos()
    → GameEngine.request_move()
        → RuleEngine.is_legal()         # בדיקת חוקיות
        → PendingMove נוסף ל-GameState
    → advance_time() (כל פריים)
        → RealTimeArbiter.advance()
            → CollisionResolver         # head-on + simultaneous
            → _apply()                  # מזיז על הלוח
            → listeners notified        # Observer
```

---

## זרימת רנדור (60fps)

```
gui_app.run() loop
    → StateManager.update(elapsed_ms)   # מקדם זמן דרך bridge
    → Renderer.draw(board, state, ...)
        → PieceRenderer.draw_all()
            → _draw_stationary()        # כלים רגילים + cooldown overlay
            → _draw_moving()            # interpolation בין source ל-target
            → _draw_airborne()          # כלים באוויר
        → PanelRenderer.draw()          # פאנל צד עם MoveLogger data
```

---

## Real-Time Logic — נקודות מפתח

| נושא | איפה | איך |
|---|---|---|
| זמן תנועה | `GameEngine.request_move` | `arrival = now + MOVE_DURATION * chebyshev_distance` |
| Cooldown | `RealTimeArbiter._apply` | `cooldowns[target] = arrival + MOVE_DURATION` |
| Head-on collision | `CollisionResolver.resolve_head_on` | מי הוגש מאוחר יותר (seq גבוה) — מבוטל |
| Simultaneous arrival | `CollisionResolver.find_simultaneous` | שני כלים על אותו target באותו זמן — שניהם נמחקים |
| Airborne collision | `RealTimeArbiter._apply` case 2 | כלי נוחת על target שכלי אויב מגיע אליו — source נמחק |
| Pawn promotion | `RealTimeArbiter._apply` | אחרי כל מהלך רגיל בודק שורה אחרונה |

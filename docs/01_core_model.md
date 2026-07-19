# 01 — Core Model & Infrastructure

---

## constants.py

קבועים גלובליים לכל הפרויקט.

| משתנה | ערך | תיאור |
|---|---|---|
| `CELL_SIZE` | 100 | גודל תא בפיקסלים |
| `MIN_CELL_SIZE` | 40 | מינימום זום |
| `MAX_CELL_SIZE` | 150 | מקסימום זום |
| `ZOOM_STEP` | 5 | פיקסלים לשינוי בכל לחיצת +/- |
| `MOVE_DURATION` | 1000 | זמן תנועה של כלי (ms) |
| `PIECE_POINTS` | dict | ערך נקודות לכל סוג כלי (P=1, N=3, B=3, R=5, Q=9, K=0) |
| `IMAGES_DIR` | Path | תיקיית תמונות הלוח |
| `PIECES_DIR` | Path | תיקיית ספרייטים של הכלים |
| `BOARD_IMAGE` | Path | נתיב לתמונת הלוח |

---

## exceptions.py

היררכיית שגיאות מותאמות. כולן יורשות מ-`ChessError`.

```
ChessError
├── BoardParseError
│   ├── EmptyRowError          — שורה ריקה בהגדרת הלוח
│   ├── RowWidthMismatchError  — מספר עמודות שגוי (שומר expected, got)
│   └── UnknownTokenError      — טוקן לא מוכר (שומר token)
├── InvalidNotationError       — סימון שחמט לא תקין (שומר notation)
└── OutOfBoundsError           — מיקום מחוץ לגבולות (שומר row, col)
```

---

## logger.py

- `logger` — `logging.getLogger("chess")`
- פלט ל-stderr (לא מפריע ל-stdout שמשמש להדפסת לוח)
- פורמט: `HH:MM:SS [LEVEL] chess: message`

---

## core/model/position.py

### `Position` (dataclass, frozen=True)
קואורדינטה בלתי-ניתנת לשינוי על הלוח. `frozen=True` מאפשר שימוש כ-dict key ו-set member.

| שדה | סוג | תיאור |
|---|---|---|
| `row` | int | שורה (0 = שורה עליונה) |
| `col` | int | עמודה (0 = עמודה שמאלית) |

- `__iter__` — מאפשר `row, col = pos`

### פונקציות עזר
- `to_chess_notation(pos, board_rows)` — ממיר Position ל-`"e2"` וכד'
- `from_chess_notation(notation, board_rows)` — ממיר `"e2"` ל-Position

---

## core/model/piece.py

### `Color` (Enum)
- `WHITE = "w"`, `BLACK = "b"`

### `PieceType` (Enum)
- `KING="K"`, `QUEEN="Q"`, `ROOK="R"`, `BISHOP="B"`, `KNIGHT="N"`, `PAWN="P"`

### קבועים
- `BLOCKABLE` — `{ROOK, BISHOP, QUEEN}` — כלים שניתן לחסום
- `VALID_COLORS`, `VALID_PIECE_TYPES` — לולידציה בפרסור

### `Piece` (dataclass, frozen=True)

| שדה/מתודה | תיאור |
|---|---|
| `color: Color` | צבע הכלי |
| `type: PieceType` | סוג הכלי |
| `from_str("wQ")` | static — יוצר Piece מ-2 תווים (תו ראשון=צבע, שני=סוג) |
| `to_str()` | מחזיר `"wQ"` וכד' |
| `same_color(other)` | האם אותו צבע |
| `is_king` | property |
| `is_pawn` | property |
| `is_blockable` | property — האם ניתן לחסום (רץ/רגלי/מלכה) |

---

## core/model/piece_status.py
**Design Pattern: Strategy**

כל סטטוס מגדיר את ההתנהגות שלו — הקורא משתמש ב-`can_act()` בלי לדעת את הסטטוס הקונקרטי.

### `PieceStatus` (ABC)
| מתודה | תיאור |
|---|---|
| `can_act()` | האם הכלי יכול לזוז עכשיו |
| `name()` | שם לצורך לוגינג |
| `sprite_state(pos, game_state)` | שם אנימציה לרנדור |

### `IdleStatus`
- `can_act()` → `True`
- `sprite_state()` → `"idle"`

### `InFlightStatus`
- `can_act()` → `False`
- `sprite_state()` → `"jump"` אם הכלי ב-airborne, אחרת `"move"`

### `OnCooldownStatus`
- נוצר עם `until: int` — זמן סיום הקולדאון
- `can_act()` → `False`
- `sprite_state()` → `"long_rest"` אם נשאר יותר מ-MOVE_DURATION, אחרת `"short_rest"`

---

## core/model/board.py

### `Board`
מטריצת הלוח הפיזי. **לא יודע חוקי שחמט** — רק פעולות פיזיות.

| שדה | תיאור |
|---|---|
| `matrix` | רשימה דו-מימדית של `Piece | None` |
| `expected_cols` | מספר עמודות (נקבע בשורה הראשונה) |

**בנייה:**
- `add_parsed_row(row)` — מוסיף שורה למטריצה

**שאילתות:**
- `is_inside(pos)` — האם בתוך גבולות הלוח
- `get_piece(pos)` → `Piece | None`
- `set_piece(pos, piece)` — מציב כלי
- `same_color(p1, p2)` — האם שני כלים באותו צבע

**נתיבים וחסימות:**
- `path(source, target)` → כל המיקומים בין source ל-target (כולל target, לא כולל source). תומך בקווים ישרים ואלכסונים בלבד.
- `intermediate_positions(source, target)` → כמו path אבל ללא target — לבדיקת חוסמים
- `has_blockers(source, target)` → `True` אם יש כלי בדרך

**פעולות:**
- `move_piece(source, target)` — מזיז כלי, מנקה source
- `remove_piece(pos)` — מסיר כלי (לכידה/התנגשות)
- `promote_pawn(pos)` — מקדם רגלי למלכה אם הגיע לשורה אחרונה (לבן בשורה 0, שחור בשורה אחרונה)

---

## core/model/game_state.py

### `PendingMove` (dataclass, frozen=True)
מהלך שהוגש אך טרם בוצע.

| שדה | תיאור |
|---|---|
| `source` | מיקום מקור |
| `target` | מיקום יעד |
| `arrival` | זמן הגעה (ms) |
| `seq` | מספר סידורי — לפתרון קונפליקטים (מי הוגש ראשון) |

### `AirbornePiece` (dataclass, frozen=True)
כלי שקפץ לאוויר.

| שדה | תיאור |
|---|---|
| `cell` | התא שממנו קפץ |
| `landing_time` | זמן נחיתה (ms) |

### `GameState` (dataclass)
סנאפשוט מלא של מצב המשחק בזמן אמת. **מוטציה** — מתעדכן כל הזמן.

| שדה | תיאור |
|---|---|
| `current_time` | שעון המשחק (ms) |
| `pending_moves` | רשימת מהלכים בדרך |
| `airborne` | רשימת כלים באוויר |
| `cooldowns` | dict: Position → זמן סיום קולדאון |
| `game_over` | האם המשחק הסתיים |
| `_seq` | מונה פנימי למהלכים |

**מתודות:**
- `next_seq()` — מחזיר מספר סידורי הבא ומקדם את המונה
- `get_status(pos)` → `PieceStatus` — בסדר עדיפות: pending_move > airborne > cooldown > idle
- `cleanup_cooldowns()` — מנקה קולדאונים שפגו (מניעת זיכרון בלתי מוגבל)
- `is_busy(pos)` → `bool` — קיצור ל-`not get_status(pos).can_act()`

---

## core/board_io/board_parser.py

### `parse_row(line_str, expected_cols)` → `list[Piece | None]`
מפרסר שורת טקסט לרשימת כלים.
- מפצל לפי רווחים
- `.` → `None`
- `"wQ"` → `Piece(WHITE, QUEEN)`
- זורק `EmptyRowError`, `RowWidthMismatchError`, `UnknownTokenError` בהתאם

---

## core/board_io/board_printer.py

### `print_board(board)`
מדפיס את הלוח ל-stdout. כל שורה: כלים מופרדים ברווח, ריק = `.`.

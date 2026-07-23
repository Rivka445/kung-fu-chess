import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
from client.graphics.unicode_text import draw_unicode_text


def _blank_canvas():
    canvas = np.zeros((120, 200, 4), dtype=np.uint8)
    canvas[..., 3] = 255
    return canvas


def _ink_rows(canvas):
    """Row range where drawing actually changed the (black) background color."""
    changed = np.any(canvas[..., :3] != 0, axis=2)
    rows = np.where(changed.any(axis=1))[0]
    return rows.min(), rows.max()


def test_draw_is_translation_invariant_in_y():
    c1 = _blank_canvas()
    draw_unicode_text(c1, "Hello", 10, 50, font_size_px=24)
    top1, bottom1 = _ink_rows(c1)

    c2 = _blank_canvas()
    draw_unicode_text(c2, "Hello", 10, 70, font_size_px=24)
    top2, bottom2 = _ink_rows(c2)

    assert bottom2 - bottom1 == 20
    assert top2 - top1 == 20


def test_baseline_alignment_across_scripts():
    """
    Regression test: different scripts have different ascent (rise above the
    baseline) — Hebrew has none of the tall ascenders Latin capitals have. A
    previous bug ignored the font's ascent metric entirely, so Hebrew text
    landed far below where Latin text at the same y would sit. Both should
    share (approximately) the same baseline row.
    """
    latin = _blank_canvas()
    draw_unicode_text(latin, "Bob", 10, 50, font_size_px=24)
    _, latin_bottom = _ink_rows(latin)

    hebrew = _blank_canvas()
    draw_unicode_text(hebrew, "בוב", 10, 50, font_size_px=24)
    _, hebrew_bottom = _ink_rows(hebrew)

    assert abs(int(latin_bottom) - int(hebrew_bottom)) <= 3


def test_empty_text_is_noop():
    canvas = _blank_canvas()
    before = canvas.copy()
    draw_unicode_text(canvas, "", 10, 50)
    assert np.array_equal(canvas, before)

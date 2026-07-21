"""
Unicode-capable text drawing for the BGRA canvas.

cv2.putText only supports its built-in Hershey fonts, which are ASCII-only —
any non-Latin script (Hebrew usernames, for example) silently renders as '?'.
This draws text with a PIL TrueType font instead, then composites it onto the
canvas, so any script the font supports shows up correctly.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_PATH = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "arial.ttf")
_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def _get_font(size_px: int) -> ImageFont.FreeTypeFont:
    font = _FONT_CACHE.get(size_px)
    if font is None:
        font = ImageFont.truetype(_FONT_PATH, size_px)
        _FONT_CACHE[size_px] = font
    return font


def draw_unicode_text(bg: np.ndarray, text: str, x: int, y: int,
                       font_size_px: int = 20, color=(0, 200, 255, 255)) -> None:
    """Draw `text` onto BGRA canvas `bg` at baseline-left (x, y), matching cv2.putText's origin convention."""
    if not text:
        return
    font = _get_font(font_size_px)
    ascent, _descent = font.getmetrics()
    measurer = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    left, top, right, bottom = measurer.textbbox((0, 0), text, font=font)
    w, h = right - left + 2, bottom - top + 2
    if w <= 0 or h <= 0:
        return

    b, g, r = color[0], color[1], color[2]
    a = color[3] if len(color) > 3 else 255

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).text((-left + 1, -top + 1), text, font=font, fill=(r, g, b, a))
    patch = np.asarray(overlay)

    # textbbox's (left, top) is relative to PIL's default "ascender-line" origin, not
    # the baseline — without subtracting `ascent` here, short scripts with little rise
    # above the baseline (e.g. Hebrew, which has no ascenders) land much lower than
    # (x, y) implies, since their small `top` offset barely corrects for it.
    H, W = bg.shape[:2]
    dst_x, dst_y = x + left, y - ascent + top - 1
    x1, y1 = max(dst_x, 0), max(dst_y, 0)
    x2, y2 = min(dst_x + w, W), min(dst_y + h, H)
    if x2 <= x1 or y2 <= y1:
        return
    sx1, sy1 = x1 - dst_x, y1 - dst_y
    sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

    roi = bg[y1:y2, x1:x2]
    sub = patch[sy1:sy2, sx1:sx2]
    alpha = sub[..., 3:4].astype(np.float32) / 255.0
    bgr = sub[..., [2, 1, 0]].astype(np.float32)
    roi[..., :3] = (alpha * bgr + (1 - alpha) * roi[..., :3]).astype(np.uint8)
    roi[..., 3] = np.maximum(roi[..., 3], sub[..., 3])

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pytest
from client.graphics.img import Img


def _opaque_square(size=10, color=(10, 20, 30, 255)):
    """A fully-opaque BGRA square used as a draw_on source."""
    img = Img()
    img.img = np.full((size, size, 4), color, dtype=np.uint8)
    return img


def _half_alpha_square(size=10, color=(10, 20, 30, 128)):
    img = Img()
    img.img = np.full((size, size, 4), color, dtype=np.uint8)
    return img


def test_create_blank_is_transparent_bgra():
    canvas = Img().create_blank(40, 20)
    assert canvas.img.shape == (20, 40, 4)
    assert canvas.img.dtype == np.uint8
    assert np.all(canvas.img == 0)


def test_draw_on_places_opaque_pixels_at_offset():
    canvas = Img().create_blank(30, 30)
    src = _opaque_square(size=5, color=(10, 20, 30, 255))
    src.draw_on(canvas, 4, 6)

    # Inside the pasted region — fully replaced by source color.
    assert list(canvas.img[6, 4]) == [10, 20, 30, 255]
    assert list(canvas.img[10, 8]) == [10, 20, 30, 255]
    # Outside the pasted region — untouched (still transparent).
    assert list(canvas.img[0, 0]) == [0, 0, 0, 0]


def test_draw_on_blends_partial_alpha():
    canvas = Img().create_blank(10, 10)
    canvas.img[:] = (100, 100, 100, 255)
    src = _half_alpha_square(size=4, color=(0, 0, 0, 128))
    src.draw_on(canvas, 0, 0)

    b, g, r, a = canvas.img[0, 0]
    mask = 128 / 255.0
    expected = round((1 - mask) * 100)
    assert abs(int(b) - expected) <= 1
    assert int(a) == 255  # max(existing 255, source 128)


def test_draw_on_clips_to_canvas_bounds_without_raising():
    canvas = Img().create_blank(10, 10)
    src = _opaque_square(size=5, color=(1, 2, 3, 255))
    # Fully off-canvas in every direction — must not raise or resize the canvas.
    src.draw_on(canvas, -10, -10)
    src.draw_on(canvas, 100, 100)
    assert canvas.img.shape == (10, 10, 4)

    # Partially off the top-left corner — only the visible slice should be drawn.
    canvas2 = Img().create_blank(10, 10)
    src.draw_on(canvas2, -2, -2)
    assert list(canvas2.img[0, 0]) == [1, 2, 3, 255]


def test_draw_on_requires_both_images_loaded():
    canvas = Img()
    src = _opaque_square()
    with pytest.raises(ValueError):
        src.draw_on(canvas, 0, 0)


def test_draw_on_with_outline_adds_border_and_draws_source():
    # Dilation happens within the source image's own array, so the source needs
    # transparent padding around the opaque shape for an outline to have anywhere
    # to appear — a shape that fills its whole array leaves the dilate nothing to grow into.
    src = Img().create_blank(20, 20)
    src.img[7:13, 7:13] = (50, 60, 70, 255)
    canvas = Img().create_blank(20, 20)

    src.draw_on_with_outline(canvas, 0, 0, color=(255, 255, 255), thickness=2)

    # Source pixels are drawn on top, unchanged.
    assert list(canvas.img[7, 7]) == [50, 60, 70, 255]
    # Just outside the opaque shape (within the dilation radius) — outline painted.
    assert canvas.img[7, 5][3] > 0
    # Far outside the dilation radius — untouched.
    assert canvas.img[0, 0][3] == 0


def test_put_text_does_not_raise_and_modifies_canvas():
    canvas = Img().create_blank(100, 40)
    before = canvas.img.copy()
    canvas.put_text("X", 5, 20, 1.0)
    assert not np.array_equal(before, canvas.img)


def test_put_text_requires_loaded_image():
    with pytest.raises(ValueError):
        Img().put_text("X", 0, 0, 1.0)


def test_read_round_trip(tmp_path):
    path = tmp_path / "sample.png"
    original = np.zeros((8, 12, 4), dtype=np.uint8)
    original[..., :3] = (5, 6, 7)
    original[..., 3] = 255
    cv2.imwrite(str(path), original)

    loaded = Img().read(str(path))
    assert loaded.img.shape == (8, 12, 4)


def test_read_resizes_with_keep_aspect(tmp_path):
    path = tmp_path / "wide.png"
    original = np.full((10, 20, 4), 255, dtype=np.uint8)
    cv2.imwrite(str(path), original)

    loaded = Img().read(str(path), size=(10, 10), keep_aspect=True)
    # 20x10 scaled to fit within 10x10 keeping aspect -> 10 wide x 5 tall.
    assert loaded.img.shape[1] == 10
    assert loaded.img.shape[0] == 5


def test_read_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        Img().read("no/such/file.png")

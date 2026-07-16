from __future__ import annotations
import pathlib
import cv2
import numpy as np


def _to_bgra(img):
    if img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


class Img:
    def __init__(self):
        self.img = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]
            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h
            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    def create_blank(self, width: int, height: int) -> "Img":
        """Create a blank BGRA canvas."""
        self.img = np.zeros((height, width, 4), dtype=np.uint8)
        return self

    def draw_on(self, other: "Img", x: int, y: int):
        if self.img is None or other.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        # Ensure both are BGRA
        src = _to_bgra(self.img)
        dst = _to_bgra(other.img)

        h, w = src.shape[:2]
        H, W = dst.shape[:2]

        # Clip to canvas bounds
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, W), min(y + h, H)
        if x2 <= x1 or y2 <= y1:
            return

        sx1, sy1 = x1 - x, y1 - y
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

        roi = dst[y1:y2, x1:x2]
        patch = src[sy1:sy2, sx1:sx2]

        b, g, r, a = cv2.split(patch)
        mask = a / 255.0
        for c in range(3):
            roi[..., c] = ((1 - mask) * roi[..., c] + mask * patch[..., c]).astype(np.uint8)
        roi[..., 3] = np.maximum(roi[..., 3], a)

        other.img = dst

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Chess", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

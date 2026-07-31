"""
Eraser tool - stamps transparent alpha to clear pixels.
"""
from __future__ import annotations
import numpy as np
from typing import Tuple, List
from core.canvas import TiledCanvas


class EraserTool:
    def __init__(self) -> None:
        self.size = 24
        self.hardness = 1.0
        self.spacing = 0.25

    def _make_stamp(self) -> np.ndarray:
        r = self.size / 2.0
        diameter = int(np.ceil(self.size))
        y, x = np.ogrid[-r + 0.5: -r + 0.5 + diameter, -r + 0.5: -r + 0.5 + diameter]
        dist = np.sqrt(x * x + y * y)
        alpha = np.clip(1.0 - (dist / r), 0.0, 1.0)
        alpha[dist > r] = 0.0
        stamp = np.zeros((diameter, diameter, 4), dtype=np.uint8)
        stamp[..., 3] = (alpha * 255.0).astype(np.uint8)
        return stamp

    def stroke(self, p0: Tuple[float, float], p1: Tuple[float, float], canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        stamp = self._make_stamp()
        radius = self.size / 2.0
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dist = np.hypot(dx, dy)
        step = max(1.0, radius * self.spacing)
        count = max(1, int(np.ceil(dist / step)))
        edits = []
        for i in range(count + 1):
            t = i / max(1, count)
            x = p0[0] + dx * t
            y = p0[1] + dy * t
            px = int(np.floor(x - stamp.shape[1] / 2))
            py = int(np.floor(y - stamp.shape[0] / 2))
            canvas.blit_array(px, py, stamp)
            # naive edit capture (prev assumed zero)
            # capture overlapping tiles
            h, w, _ = stamp.shape
            x0, y0 = px, py
            x1, y1 = px + w, py + h
            tx0 = canvas._tile_index(x0, y0)[0]
            ty0 = canvas._tile_index(x0, y0)[1]
            tx1 = canvas._tile_index(x1 - 1, y1 - 1)[0]
            ty1 = canvas._tile_index(x1 - 1, y1 - 1)[1]
            for ty in range(ty0, ty1 + 1):
                for tx in range(tx0, tx1 + 1):
                    tile = canvas.get_tile(tx, ty, create=True)
                    new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                    prev = np.zeros_like(new)
                    edits.append((tx, ty, prev, new))
        return edits

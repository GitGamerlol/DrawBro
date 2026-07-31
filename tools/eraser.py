"""
Eraser tool updated to capture per-tile prev/new for undo and to erase by stamping transparent alpha.
"""
from __future__ import annotations

import numpy as np
from typing import Tuple, List
from core.canvas import TiledCanvas


class EraserTool:
    def __init__(self) -> None:
        self.size: float = 24.0
        self.hardness: float = 1.0
        self.spacing: float = 0.25

    def _make_stamp_alpha(self) -> np.ndarray:
        r = self.size / 2.0
        diameter = int(np.ceil(self.size))
        ys = np.arange(diameter) - (diameter / 2.0 - 0.5)
        xs = np.arange(diameter) - (diameter / 2.0 - 0.5)
        y, x = np.meshgrid(ys, xs, indexing="ij")
        dist = np.sqrt(x * x + y * y)
        alpha = np.clip(1.0 - (dist / r), 0.0, 1.0)
        alpha[dist > r] = 0.0
        return (alpha * 255.0).astype(np.uint8)

    def stroke(self, p0: Tuple[float, float], p1: Tuple[float, float], canvas: TiledCanvas, pressure: float = 1.0) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        alpha_mask = self._make_stamp_alpha()
        stamp_h, stamp_w = alpha_mask.shape
        # Create an RGBA stamp where RGB is ignored and alpha is the mask
        stamp = np.zeros((stamp_h, stamp_w, 4), dtype=np.uint8)
        stamp[..., 3] = (alpha_mask.astype(np.float32) * pressure).clip(0, 255).astype(np.uint8)

        r = self.size / 2.0
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dist = np.hypot(dx, dy)
        step = max(1.0, r * self.spacing)
        count = max(1, int(np.ceil(dist / step)))
        positions: List[Tuple[int, int]] = []
        for i in range(count + 1):
            t = i / max(1, count)
            x = p0[0] + dx * t
            y = p0[1] + dy * t
            px = int(np.floor(x - stamp_w / 2))
            py = int(np.floor(y - stamp_h / 2))
            positions.append((px, py))

        if not positions:
            return []

        # Determine affected tiles
        tile_coords = set()
        for (px, py) in positions:
            x0, y0 = px, py
            x1, y1 = px + stamp_w, py + stamp_h
            tx0, ty0 = canvas._tile_index(x0, y0)
            tx1, ty1 = canvas._tile_index(x1 - 1, y1 - 1)
            for ty in range(ty0, ty1 + 1):
                for tx in range(tx0, tx1 + 1):
                    tile_coords.add((tx, ty))

        # Capture prev
        prev_map = {}
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            prev_map[(tx, ty)] = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)

        # Apply stamps
        for (px, py) in positions:
            canvas.blit_array(px, py, stamp)

        # Capture new buffers
        edits = []
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            prev = prev_map[(tx, ty)]
            edits.append((tx, ty, prev, new))

        return edits

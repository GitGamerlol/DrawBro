from __future__ import annotations

import numpy as np
from typing import Tuple, List
from core.canvas import TiledCanvas
import cv2


class SmoothTool:
    def __init__(self) -> None:
        self.radius = 5
        self.mode = "gaussian"  # or "median"

    def apply_at(self, cx: int, cy: int, canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        # Build bounding box
        r = int(max(1, self.radius))
        x0 = cx - r
        y0 = cy - r
        x1 = cx + r + 1
        y1 = cy + r + 1
        w = x1 - x0
        h = y1 - y0
        # Assemble source array from tiles
        src = np.zeros((h, w, 4), dtype=np.uint8)
        for ty in range(canvas._tile_index(y0, 0)[1], canvas._tile_index(y1 - 1, 0)[1] + 1):
            pass
        # Simpler approach: iterate over pixels (inefficient) but acceptable for small radii
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                px = canvas.get_pixel(xx, yy)
                src[yy - y0, xx - x0] = np.array(px, dtype=np.uint8)
        # Apply filter on color channels
        if self.mode == "gaussian":
            k = max(1, (2 * (self.radius // 2) + 1))
            blurred = cv2.GaussianBlur(src, (k, k), sigmaX=0)
        else:
            k = max(1, (2 * (self.radius // 2) + 1))
            # median requires single-channel; apply per-channel
            channels = []
            for c in range(4):
                ch = cv2.medianBlur(src[..., c], k)
                channels.append(ch)
            blurred = np.stack(channels, axis=-1)
        # Apply blurred back and capture per-tile edits
        tiles = {}
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                tx, ty = canvas._tile_index(xx, yy)
                key = (tx, ty)
                if key not in tiles:
                    tile = canvas.get_tile(tx, ty, create=True)
                    prev = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                    tiles[key] = prev
                local_x = xx - tx * canvas.tile_size
                local_y = yy - ty * canvas.tile_size
                tile = canvas.get_tile(tx, ty, create=True)
                tile.ensure_data()
                tile.data[local_y, local_x] = blurred[yy - y0, xx - x0].astype(np.uint8)
        edits = []
        for (tx, ty), prev in tiles.items():
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros_like(prev)
            edits.append((tx, ty, prev, new))
        return edits

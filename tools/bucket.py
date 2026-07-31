from __future__ import annotations

import numpy as np
from typing import Tuple, List
from core.canvas import TiledCanvas
from core.commands import TileEditCommand
import collections


class BucketTool:
    def __init__(self) -> None:
        self.tolerance = 0  # exact match only for now

    def _color_eq(self, a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
        return a == b

    def fill(self, x: int, y: int, canvas: TiledCanvas, color: Tuple[int, int, int, int]) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        """Perform a flood fill starting at world pixel (x,y) with color (r,g,b,a).

        Returns edits list like (tx,ty,prev,new).
        Note: naive implementation (per-pixel BFS). Capped to avoid runaway fills.
        """
        x0 = int(round(x))
        y0 = int(round(y))
        target = canvas.get_pixel(x0, y0)
        if self._color_eq(target, color):
            return []
        # BFS
        max_pixels = 2_000_000  # safety cap
        q = collections.deque()
        q.append((x0, y0))
        visited = set()
        affected_pixels = []
        while q and len(visited) < max_pixels:
            px, py = q.popleft()
            if (px, py) in visited:
                continue
            visited.add((px, py))
            cur = canvas.get_pixel(px, py)
            if not self._color_eq(cur, target):
                continue
            affected_pixels.append((px, py))
            # neighbors 4-connected
            q.append((px + 1, py))
            q.append((px - 1, py))
            q.append((px, py + 1))
            q.append((px, py - 1))
        if not affected_pixels:
            return []
        # Group affected pixels by tile and create prev/new tile buffers
        tiles = {}
        for px, py in affected_pixels:
            tx = canvas._tile_index(px, py)[0]
            ty = canvas._tile_index(px, py)[1]
            key = (tx, ty)
            if key not in tiles:
                tile = canvas.get_tile(tx, ty, create=True)
                prev = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                tiles[key] = prev
        # Apply changes directly to canvas tiles
        for px, py in affected_pixels:
            tx, ty = canvas._tile_index(px, py)
            local_x = px - tx * canvas.tile_size
            local_y = py - ty * canvas.tile_size
            tile = canvas.get_tile(tx, ty, create=True)
            tile.ensure_data()
            tile.data[local_y, local_x] = np.array(color, dtype=np.uint8)
        # Assemble edits
        edits = []
        for (tx, ty), prev in tiles.items():
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros_like(prev)
            edits.append((tx, ty, prev, new))
        return edits

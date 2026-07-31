"""
Pen tool implementation with proper undo capture and colorization.

This implementation:
- Generates a circular stamp mask based on size and hardness.
- Colorizes the stamp using the tool's current color and opacity.
- Samples along the stroke with spacing and accumulates stamp positions.
- Captures "prev" buffers for all affected tiles before any stamping,
  applies all stamps, then reads back "new" buffers for the same tiles.
- Returns edits: list of (tx, ty, prev, new) ready for TileEditCommand.

Pressure support: callers may pass a `pressure` value in [0,1]; it's multiplied into opacity.
"""
from __future__ import annotations

import numpy as np
from typing import Tuple, List
from core.canvas import TiledCanvas


class PenTool:
    def __init__(self) -> None:
        self.size: float = 24.0
        self.opacity: float = 1.0  # base opacity 0..1
        self.hardness: float = 0.8  # 0..1
        self.spacing: float = 0.25  # spacing in brush radii
        # color as RGBA 0..255
        self.color: Tuple[int, int, int, int] = (0, 0, 0, 255)

    def _make_stamp_alpha(self) -> np.ndarray:
        """Return a 2D alpha mask (0..255 uint8) for the brush stamp based on size & hardness."""
        r = self.size / 2.0
        diameter = int(np.ceil(self.size))
        # Create coordinates centered
        ys = np.arange(diameter) - (diameter / 2.0 - 0.5)
        xs = np.arange(diameter) - (diameter / 2.0 - 0.5)
        y, x = np.meshgrid(ys, xs, indexing="ij")
        dist = np.sqrt(x * x + y * y)
        inner = r * self.hardness
        # linear falloff from inner..r
        alpha = np.clip((r - dist) / (r - inner + 1e-8), 0.0, 1.0)
        alpha[dist > r] = 0.0
        alpha_u8 = (alpha * 255.0).astype(np.uint8)
        return alpha_u8

    def _colorize_stamp(self, alpha_mask: np.ndarray, pressure: float = 1.0) -> np.ndarray:
        h, w = alpha_mask.shape
        stamp = np.zeros((h, w, 4), dtype=np.uint8)
        r, g, b, a = self.color
        # combined alpha = mask * base_opacity * pressure
        combined_alpha = (alpha_mask.astype(np.float32) * (self.opacity * pressure)).clip(0, 255).astype(np.uint8)
        stamp[..., 0] = r
        stamp[..., 1] = g
        stamp[..., 2] = b
        stamp[..., 3] = combined_alpha
        return stamp

    def stroke(self, p0: Tuple[float, float], p1: Tuple[float, float], canvas: TiledCanvas, pressure: float = 1.0) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        """Rasterize the stroke from p0 to p1 onto the provided TiledCanvas.

        Returns a list of edits (tx, ty, prev, new) suitable for TileEditCommand.
        """
        # Generate stamp alpha mask once
        alpha_mask = self._make_stamp_alpha()
        stamp = self._colorize_stamp(alpha_mask, pressure=pressure)
        r = self.size / 2.0
        # compute positions along stroke
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
            px = int(np.floor(x - stamp.shape[1] / 2))
            py = int(np.floor(y - stamp.shape[0] / 2))
            positions.append((px, py))

        if not positions:
            return []

        # Determine affected tiles (set)
        tile_coords = set()
        stamp_h, stamp_w = stamp.shape[:2]
        for (px, py) in positions:
            x0, y0 = px, py
            x1, y1 = px + stamp_w, py + stamp_h
            tx0, ty0 = canvas._tile_index(x0, y0)
            tx1, ty1 = canvas._tile_index(x1 - 1, y1 - 1)
            for ty in range(ty0, ty1 + 1):
                for tx in range(tx0, tx1 + 1):
                    tile_coords.add((tx, ty))

        # Capture prev buffers
        edits = []
        prev_map: dict[Tuple[int, int], np.ndarray] = {}
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            if tile.data is None:
                prev = np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            else:
                prev = tile.data.copy()
            prev_map[(tx, ty)] = prev

        # Apply all stamps
        for (px, py) in positions:
            canvas.blit_array(px, py, stamp)

        # Capture new buffers and assemble edits
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            prev = prev_map[(tx, ty)]
            edits.append((tx, ty, prev, new))

        return edits

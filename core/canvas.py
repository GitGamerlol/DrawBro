"""
Tiled canvas implementation.

- Uses fixed-size tiles (default 1024x1024).
- Tiles are numpy arrays (RGBA uint8).
- Tiles are created on-demand and stored in a dict keyed by (tx, ty).
- Coordinates:
    World coordinates are in pixels; tile coordinates are integer tile indices.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Dict, Iterator, Optional


TileCoord = Tuple[int, int]  # (tx, ty)
RGBA = Tuple[int, int, int, int]


DEFAULT_TILE_SIZE = 1024


@dataclass
class Tile:
    coord: TileCoord
    size: int = DEFAULT_TILE_SIZE
    data: np.ndarray | None = None  # shape (H, W, 4), dtype=uint8

    def ensure_data(self) -> np.ndarray:
        if self.data is None:
            self.data = np.zeros((self.size, self.size, 4), dtype=np.uint8)
        return self.data

    def clear(self) -> None:
        self.data = None


class TiledCanvas:
    """
    A canvas composed of tiles. Coordinates are in pixels.
    Tiles are addressed by integer tile indices (floor division by tile_size).
    """

    def __init__(self, tile_size: int = DEFAULT_TILE_SIZE):
        self.tile_size = tile_size
        self.tiles: Dict[TileCoord, Tile] = {}
        # Optional bounds tracking for optimization (min/max tile indices that exist)
        self._min_tile: Optional[TileCoord] = None
        self._max_tile: Optional[TileCoord] = None

    def _tile_index(self, x: int, y: int) -> TileCoord:
        tx = x // self.tile_size if x >= 0 else -((-x - 1) // self.tile_size) - 1
        ty = y // self.tile_size if y >= 0 else -((-y - 1) // self.tile_size) - 1
        return tx, ty

    def _update_bounds(self, tx: int, ty: int) -> None:
        if self._min_tile is None:
            self._min_tile = (tx, ty)
            self._max_tile = (tx, ty)
            return
        min_tx, min_ty = self._min_tile
        max_tx, max_ty = self._max_tile
        self._min_tile = (min(min_tx, tx), min(min_ty, ty))
        self._max_tile = (max(max_tx, tx), max(max_ty, ty))

    def get_tile(self, tx: int, ty: int, create: bool = True) -> Tile:
        key = (tx, ty)
        tile = self.tiles.get(key)
        if tile is None:
            if not create:
                raise KeyError(f"Tile {key} not found")
            tile = Tile(coord=key, size=self.tile_size)
            tile.ensure_data()
            self.tiles[key] = tile
            self._update_bounds(tx, ty)
        return tile

    def get_tile_if_exists(self, tx: int, ty: int) -> Tile | None:
        return self.tiles.get((tx, ty))

    def set_pixel(self, x: int, y: int, color: RGBA) -> None:
        tx, ty = self._tile_index(x, y)
        tile = self.get_tile(tx, ty, create=True)
        local_x = x - tx * self.tile_size
        local_y = y - ty * self.tile_size
        tile.ensure_data()[local_y, local_x] = np.array(color, dtype=np.uint8)

    def get_pixel(self, x: int, y: int) -> RGBA:
        tx, ty = self._tile_index(x, y)
        tile = self.get_tile_if_exists(tx, ty)
        if tile is None or tile.data is None:
            return (0, 0, 0, 0)
        local_x = x - tx * self.tile_size
        local_y = y - ty * self.tile_size
        px = tile.data[local_y, local_x]
        return int(px[0]), int(px[1]), int(px[2]), int(px[3])

    def blit_array(self, x: int, y: int, arr: np.ndarray) -> None:
        """
        Blit a numpy array (H, W, 4) at world coords (x, y).
        This splits across tiles as needed.
        """
        h, w, c = arr.shape
        assert c == 4, "Expected RGBA array"
        # Loop over affected tile indices
        x0, y0 = x, y
        x1, y1 = x + w, y + h
        tx0, ty0 = self._tile_index(x0, y0)
        tx1, ty1 = self._tile_index(x1 - 1, y1 - 1)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                tile = self.get_tile(tx, ty, create=True)
                tile_arr = tile.ensure_data()
                # Intersection in tile-local coords
                tile_x0 = max(0, x0 - tx * self.tile_size)
                tile_y0 = max(0, y0 - ty * self.tile_size)
                tile_x1 = min(self.tile_size, x1 - tx * self.tile_size)
                tile_y1 = min(self.tile_size, y1 - ty * self.tile_size)
                src_x0 = tile_x0 + tx * self.tile_size - x0
                src_y0 = tile_y0 + ty * self.tile_size - y0
                src_x1 = src_x0 + (tile_x1 - tile_x0)
                src_y1 = src_y0 + (tile_y1 - tile_y0)
                src_slice = arr[src_y0:src_y1, src_x0:src_x1]
                dst_slice = tile_arr[tile_y0:tile_y1, tile_x0:tile_x1]
                # Simple alpha composite: src over dst
                src_alpha = src_slice[..., 3:4].astype(np.float32) / 255.0
                dst_alpha = dst_slice[..., 3:4].astype(np.float32) / 255.0
                out_alpha = src_alpha + dst_alpha * (1 - src_alpha)
                # Avoid division by zero
                with np.errstate(invalid="ignore", divide="ignore"):
                    out_rgb = (src_slice[..., :3].astype(np.float32) * src_alpha +
                               dst_slice[..., :3].astype(np.float32) * dst_alpha * (1 - src_alpha))
                    out_rgb = np.where(out_alpha > 0, out_rgb / out_alpha, 0)
                dst_slice[..., :3] = np.clip(out_rgb, 0, 255).astype(np.uint8)
                dst_slice[..., 3] = np.clip(out_alpha[..., 0] * 255.0, 0, 255).astype(np.uint8)
                tile_arr[tile_y0:tile_y1, tile_x0:tile_x1] = dst_slice

    def iter_tiles(self) -> Iterator[Tile]:
        yield from self.tiles.values()

    def iter_tiles_in_rect(self, x: int, y: int, w: int, h: int) -> Iterator[Tile]:
        x1, y1 = x + w, y + h
        tx0, ty0 = self._tile_index(x, y)
        tx1, ty1 = self._tile_index(x1 - 1, y1 - 1)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                tile = self.get_tile_if_exists(tx, ty)
                if tile and tile.data is not None:
                    yield tile

    def clear(self) -> None:
        self.tiles.clear()
        self._min_tile = None
        self._max_tile = None

from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, Optional, List
from core.canvas import TiledCanvas


class ShapeToolBase:
    """Base API for shape tools.

    Usage:
    - call start((x,y)) in world coords when mouse pressed
    - call update((x,y)) as mouse moves
    - call get_preview() -> (arr, top_left_world_x, top_left_world_y) to obtain an RGBA preview image and its top-left world coordinate
    - call finish(canvas) to rasterize the final shape into the canvas and return edits list (tx,ty,prev,new)
    """

    def __init__(self) -> None:
        self.start_pt: Optional[Tuple[float, float]] = None
        self.end_pt: Optional[Tuple[float, float]] = None
        self.stroke_width: int = 3
        self.stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self.fill: bool = False
        self.fill_color: Tuple[int, int, int, int] = (0, 0, 0, 255)

    def start(self, p: Tuple[float, float]) -> None:
        self.start_pt = p
        self.end_pt = p

    def update(self, p: Tuple[float, float]) -> None:
        self.end_pt = p

    def _bbox(self) -> Tuple[int, int, int, int]:
        if self.start_pt is None or self.end_pt is None:
            return 0, 0, 1, 1
        x0 = int(min(self.start_pt[0], self.end_pt[0]))
        y0 = int(min(self.start_pt[1], self.end_pt[1]))
        x1 = int(max(self.start_pt[0], self.end_pt[0]))
        y1 = int(max(self.start_pt[1], self.end_pt[1]))
        # pad by stroke width
        pad = int(self.stroke_width + 2)
        return x0 - pad, y0 - pad, x1 - x0 + pad * 2, y1 - y0 + pad * 2

    def get_preview(self) -> Tuple[np.ndarray, int, int]:
        """Return (rgba_arr, top_left_x, top_left_y) for preview drawing."""
        raise NotImplementedError

    def finish(self, canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        """Rasterize into canvas and return edits."""
        raise NotImplementedError


class LineTool(ShapeToolBase):
    def __init__(self) -> None:
        super().__init__()
        self.stroke_width = 3
        self.stroke_color = (0, 0, 0, 255)

    def _render_to_array(self, bbox: Tuple[int, int, int, int], antialias: bool = True) -> np.ndarray:
        x0, y0, w, h = bbox
        img = np.zeros((h, w, 4), dtype=np.uint8)
        if self.start_pt is None or self.end_pt is None:
            return img
        # convert to local coordinates
        sx = int(round(self.start_pt[0] - x0))
        sy = int(round(self.start_pt[1] - y0))
        ex = int(round(self.end_pt[0] - x0))
        ey = int(round(self.end_pt[1] - y0))
        # Draw mask on alpha channel using cv2.line on single channel
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.line(mask, (sx, sy), (ex, ey), color=255, thickness=self.stroke_width, lineType=cv2.LINE_AA if antialias else cv2.LINE_8)
        # color channels
        b, g, r, a = self.stroke_color[2], self.stroke_color[1], self.stroke_color[0], self.stroke_color[3]
        img[..., 0] = r
        img[..., 1] = g
        img[..., 2] = b
        # combine mask and stroke opacity
        img[..., 3] = (mask.astype(np.float32) * (a / 255.0)).astype(np.uint8)
        return img

    def get_preview(self) -> Tuple[np.ndarray, int, int]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        return arr, bbox[0], bbox[1]

    def finish(self, canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        x, y = bbox[0], bbox[1]
        # determine tiles touched
        x0, y0 = x, y
        x1, y1 = x + bbox[2], y + bbox[3]
        tx0, ty0 = canvas._tile_index(x0, y0)
        tx1, ty1 = canvas._tile_index(x1 - 1, y1 - 1)
        tile_coords = []
        prev_map = {}
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                tile = canvas.get_tile(tx, ty, create=True)
                prev = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                prev_map[(tx, ty)] = prev
                tile_coords.append((tx, ty))
        # Blit
        canvas.blit_array(x, y, arr)
        edits = []
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            prev = prev_map[(tx, ty)]
            edits.append((tx, ty, prev, new))
        return edits


class RectangleTool(ShapeToolBase):
    def __init__(self) -> None:
        super().__init__()
        self.stroke_width = 3
        self.stroke_color = (0, 0, 0, 255)
        self.fill = False
        self.fill_color = (0, 0, 0, 255)

    def _render_to_array(self, bbox: Tuple[int, int, int, int], antialias: bool = True) -> np.ndarray:
        x0, y0, w, h = bbox
        img = np.zeros((h, w, 4), dtype=np.uint8)
        if self.start_pt is None or self.end_pt is None:
            return img
        sx = int(round(self.start_pt[0] - x0))
        sy = int(round(self.start_pt[1] - y0))
        ex = int(round(self.end_pt[0] - x0))
        ey = int(round(self.end_pt[1] - y0))
        left, top = min(sx, ex), min(sy, ey)
        right, bottom = max(sx, ex), max(sy, ey)
        mask = np.zeros((h, w), dtype=np.uint8)
        if self.fill:
            cv2.rectangle(mask, (left, top), (right, bottom), color=255, thickness=cv2.FILLED)
        if self.stroke_width > 0:
            cv2.rectangle(mask, (left, top), (right, bottom), color=255, thickness=self.stroke_width)
        # fill color takes precedence for RGB channels when fill enabled
        if self.fill:
            r, g, b, a = self.fill_color[0], self.fill_color[1], self.fill_color[2], self.fill_color[3]
            img[..., 0] = r
            img[..., 1] = g
            img[..., 2] = b
            img[..., 3] = (mask.astype(np.float32) * (a / 255.0)).astype(np.uint8)
        else:
            r, g, b, a = self.stroke_color[0], self.stroke_color[1], self.stroke_color[2], self.stroke_color[3]
            img[..., 0] = r
            img[..., 1] = g
            img[..., 2] = b
            img[..., 3] = (mask.astype(np.float32) * (a / 255.0)).astype(np.uint8)
        return img

    def get_preview(self) -> Tuple[np.ndarray, int, int]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        return arr, bbox[0], bbox[1]

    def finish(self, canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        x, y = bbox[0], bbox[1]
        x0, y0 = x, y
        x1, y1 = x + bbox[2], y + bbox[3]
        tx0, ty0 = canvas._tile_index(x0, y0)
        tx1, ty1 = canvas._tile_index(x1 - 1, y1 - 1)
        tile_coords = []
        prev_map = {}
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                tile = canvas.get_tile(tx, ty, create=True)
                prev = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                prev_map[(tx, ty)] = prev
                tile_coords.append((tx, ty))
        canvas.blit_array(x, y, arr)
        edits = []
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            prev = prev_map[(tx, ty)]
            edits.append((tx, ty, prev, new))
        return edits


class EllipseTool(ShapeToolBase):
    def __init__(self) -> None:
        super().__init__()
        self.stroke_width = 3
        self.stroke_color = (0, 0, 0, 255)
        self.fill = False
        self.fill_color = (0, 0, 0, 255)

    def _render_to_array(self, bbox: Tuple[int, int, int, int], antialias: bool = True) -> np.ndarray:
        x0, y0, w, h = bbox
        img = np.zeros((h, w, 4), dtype=np.uint8)
        if self.start_pt is None or self.end_pt is None:
            return img
        sx = int(round(self.start_pt[0] - x0))
        sy = int(round(self.start_pt[1] - y0))
        ex = int(round(self.end_pt[0] - x0))
        ey = int(round(self.end_pt[1] - y0))
        center = ((sx + ex) // 2, (sy + ey) // 2)
        axes = (max(1, abs(ex - sx) // 2), max(1, abs(ey - sy) // 2))
        mask = np.zeros((h, w), dtype=np.uint8)
        if self.fill:
            cv2.ellipse(mask, center, axes, angle=0, startAngle=0, endAngle=360, color=255, thickness=cv2.FILLED, lineType=cv2.LINE_AA if antialias else cv2.LINE_8)
        if self.stroke_width > 0:
            cv2.ellipse(mask, center, axes, angle=0, startAngle=0, endAngle=360, color=255, thickness=self.stroke_width, lineType=cv2.LINE_AA if antialias else cv2.LINE_8)
        if self.fill:
            r, g, b, a = self.fill_color[0], self.fill_color[1], self.fill_color[2], self.fill_color[3]
            img[..., 0] = r
            img[..., 1] = g
            img[..., 2] = b
            img[..., 3] = (mask.astype(np.float32) * (a / 255.0)).astype(np.uint8)
        else:
            r, g, b, a = self.stroke_color[0], self.stroke_color[1], self.stroke_color[2], self.stroke_color[3]
            img[..., 0] = r
            img[..., 1] = g
            img[..., 2] = b
            img[..., 3] = (mask.astype(np.float32) * (a / 255.0)).astype(np.uint8)
        return img

    def get_preview(self) -> Tuple[np.ndarray, int, int]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        return arr, bbox[0], bbox[1]

    def finish(self, canvas: TiledCanvas) -> List[tuple[int, int, np.ndarray, np.ndarray]]:
        bbox = self._bbox()
        arr = self._render_to_array(bbox)
        x, y = bbox[0], bbox[1]
        x0, y0 = x, y
        x1, y1 = x + bbox[2], y + bbox[3]
        tx0, ty0 = canvas._tile_index(x0, y0)
        tx1, ty1 = canvas._tile_index(x1 - 1, y1 - 1)
        tile_coords = []
        prev_map = {}
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                tile = canvas.get_tile(tx, ty, create=True)
                prev = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
                prev_map[(tx, ty)] = prev
                tile_coords.append((tx, ty))
        canvas.blit_array(x, y, arr)
        edits = []
        for (tx, ty) in tile_coords:
            tile = canvas.get_tile(tx, ty, create=True)
            new = tile.data.copy() if tile.data is not None else np.zeros((canvas.tile_size, canvas.tile_size, 4), dtype=np.uint8)
            prev = prev_map[(tx, ty)]
            edits.append((tx, ty, prev, new))
        return edits

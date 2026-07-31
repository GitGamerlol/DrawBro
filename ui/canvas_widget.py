from __future__ import annotations

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QWheelEvent, QColor
from PySide6.QtCore import Qt, QRect, Signal
import numpy as np
from typing import Optional, Tuple
import math

from core.viewport import Viewport
from core.project import Project
from core.frame import Frame
from core.history import HistoryManager
from core.commands import TileEditCommand
from tools.pen import PenTool
from tools.eraser import EraserTool


def numpy_to_qimage(arr: np.ndarray) -> QImage:
    """Convert an (H,W,4) uint8 RGBA numpy array to QImage safely.

    Ensures the array is contiguous and returns a QImage that owns its data copy (to avoid memory lifetime issues).
    """
    if arr.ndim != 3 or arr.shape[2] != 4:
        raise ValueError("Expected HxWx4 RGBA array")
    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr)
    h, w, _ = arr.shape
    # Create QImage from bytes copy to be safe across threads and lifetimes
    return QImage(arr.tobytes(), w, h, QImage.Format_RGBA8888).copy()


class CanvasWidget(QWidget):
    """Widget responsible for rendering the tiled canvas and routing input to tools.

    Signals:
        zoomChanged(float) - emitted when zoom level changes
    """

    zoomChanged = Signal(float)

    def __init__(self, project: Project, viewport: Optional[Viewport] = None, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.viewport = viewport or Viewport()
        self.setFocusPolicy(Qt.ClickFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self._dragging_pan = False
        self._last_mouse_pos: Optional[Tuple[int, int]] = None

        # Tools
        self.pen_tool = PenTool()
        self.eraser_tool = EraserTool()
        self.active_tool = self.pen_tool

        # Tools default color (black)
        self.pen_tool.color = (0, 0, 0, 255)

        # History
        self.history = HistoryManager()

        # State to accumulate tile edits while drawing
        self._current_edits: list[tuple[int, int, np.ndarray, np.ndarray]] = []

    def sizeHint(self):
        return super().sizeHint()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(50, 50, 50))
        frame = self.project.frames[0]

        # Compute world rect visible
        w, h = self.width(), self.height()
        # Top-left and bottom-right in world coords
        top_left = self.viewport.screen_to_world(0, 0)
        bottom_right = self.viewport.screen_to_world(w, h)
        wx0, wy0 = int(top_left[0]), int(top_left[1])
        wx1, wy1 = int(bottom_right[0]) + 1, int(bottom_right[1]) + 1
        view_w = wx1 - wx0
        view_h = wy1 - wy0

        # Composite and draw tiles per layer
        for layer in frame.layers:
            if not layer.visible:
                continue
            for tile in layer.canvas.iter_tiles_in_rect(wx0, wy0, view_w, view_h):
                if tile.data is None:
                    continue
                tx, ty = tile.coord
                # Avoid unnecessary full copies; ensure we don't modify tile.data
                arr = tile.data
                # Convert to QImage safely
                try:
                    qimg = numpy_to_qimage(arr)
                except Exception:
                    continue
                # Tile top-left world coords
                world_x = tx * layer.canvas.tile_size
                world_y = ty * layer.canvas.tile_size
                # Convert to screen coords
                sx, sy = self.viewport.world_to_screen(world_x, world_y)
                dest_x = int(round(sx))
                dest_y = int(round(sy))
                # Adjust for device pixel ratio
                dpr = self.devicePixelRatioF()
                if dpr != 1.0:
                    qimg.setDevicePixelRatio(dpr)
                painter.drawImage(dest_x, dest_y, qimg)

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Smooth zoom: use exponential scale per step for stable zooming
        angle = event.angleDelta().y()
        if angle == 0:
            return
        steps = angle / 120.0
        # base factor per step
        base = 1.2
        factor = math.pow(base, steps)
        pos = event.position()
        self.viewport.zoom_at(factor, pos.x(), pos.y())
        # Emit signal and request repaint of viewport area
        self.zoomChanged.emit(self.viewport.zoom)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self._dragging_pan = True
            self._last_mouse_pos = (event.x(), event.y())
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            # Start drawing
            self._last_mouse_pos = (event.x(), event.y())
            self._current_edits = []
            # Begin a capture - the active tool will capture prev tiles itself when stroke is called
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging_pan and self._last_mouse_pos is not None:
            dx = event.x() - self._last_mouse_pos[0]
            dy = event.y() - self._last_mouse_pos[1]
            # Translate pan by inverse of zoom
            self.viewport.pan_x -= dx / self.viewport.zoom
            self.viewport.pan_y -= dy / self.viewport.zoom
            self._last_mouse_pos = (event.x(), event.y())
            self.zoomChanged.emit(self.viewport.zoom)
            self.update()
            return

        buttons = event.buttons()
        if buttons & Qt.LeftButton and self._last_mouse_pos is not None:
            # Drawing
            last = self._last_mouse_pos
            current = (event.x(), event.y())
            # Convert to world coords
            lx, ly = self.viewport.screen_to_world(float(last[0]), float(last[1]))
            cx, cy = self.viewport.screen_to_world(float(current[0]), float(current[1]))
            # Ask active tool to stroke between points into the active layer's canvas
            frame = self.project.frames[0]
            if not frame.layers:
                frame.add_layer()
            layer = frame.layers[0]
            edits = self.active_tool.stroke((lx, ly), (cx, cy), layer.canvas)
            # Each edit is (tx,ty, prev, new) - accumulate
            self._current_edits.extend(edits)
            # Invalidate only affected tiles on screen
            self._invalidate_edits(edits, layer.canvas.tile_size)
            self._last_mouse_pos = current
        else:
            self._last_mouse_pos = (event.x(), event.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self._dragging_pan = False
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.LeftButton:
            # Commit current edits as a single history command
            if self._current_edits:
                cmd = TileEditCommand(self.project.frames[0].layers[0].canvas, self._current_edits)
                self.history.push(cmd)
                # After pushing, ensure the UI updates for the whole modified area (already invalidated during drawing)
                self._current_edits = []
            self.update()
        super().mouseReleaseEvent(event)

    def _invalidate_edits(self, edits: list[tuple[int, int, np.ndarray, np.ndarray]], tile_size: int) -> None:
        if not edits:
            return
        # compute bounding rect in screen coordinates for all tiles
        sx_min = None
        sy_min = None
        sx_max = None
        sy_max = None
        for tx, ty, prev, new in edits:
            world_x = tx * tile_size
            world_y = ty * tile_size
            sx0, sy0 = self.viewport.world_to_screen(world_x, world_y)
            sx1, sy1 = self.viewport.world_to_screen(world_x + tile_size, world_y + tile_size)
            x0, y0 = int(math.floor(min(sx0, sx1))), int(math.floor(min(sy0, sy1)))
            x1, y1 = int(math.ceil(max(sx0, sx1))), int(math.ceil(max(sy0, sy1)))
            if sx_min is None:
                sx_min, sy_min, sx_max, sy_max = x0, y0, x1, y1
            else:
                sx_min = min(sx_min, x0)
                sy_min = min(sy_min, y0)
                sx_max = max(sx_max, x1)
                sy_max = max(sy_max, y1)
        if sx_min is not None:
            rect = QRect(sx_min, sy_min, max(1, sx_max - sx_min), max(1, sy_max - sy_min))
            self.update(rect)

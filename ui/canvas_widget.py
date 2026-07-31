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
from PySide6.QtGui import QColor as QtColor


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
        colorPicked(QColor) - emitted when eyedropper samples a color
    """

    zoomChanged = Signal(float)
    colorPicked = Signal(QtColor)

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

        # Preview image for shape tools
        self._preview_qimage: Optional[QImage] = None
        self._preview_world_pos: Optional[Tuple[int, int]] = None

        # Reference corner picking state
        self._corner_pick_target = None
        self._corner_points: list[Tuple[float, float]] = []

    def sizeHint(self):
        return super().sizeHint()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(50, 50, 50))

        # Draw reference images first (they are not part of the artwork and won't be exported)
        for ref in getattr(self.project, "reference_images", []):
            if not getattr(ref, "visible", False):
                continue
            warped = None
            try:
                warped = ref.get_warped_rgba(self.project.width, self.project.height)
            except Exception:
                warped = None
            if warped is None:
                continue
            try:
                qimg = numpy_to_qimage(warped)
            except Exception:
                continue
            dpr = self.devicePixelRatioF()
            if dpr != 1.0:
                qimg.setDevicePixelRatio(dpr)
            # draw at world origin (0,0)
            sx, sy = self.viewport.world_to_screen(0, 0)
            painter.drawImage(int(round(sx)), int(round(sy)), qimg)

        # Compute world rect visible
        w, h = self.width(), self.height()
        # Top-left and bottom-right in world coords
        top_left = self.viewport.screen_to_world(0, 0)
        bottom_right = self.viewport.screen_to_world(w, h)
        wx0, wy0 = int(top_left[0]), int(top_left[1])
        wx1, wy1 = int(bottom_right[0]) + 1, int(bottom_right[1]) + 1
        view_w = wx1 - wx0
        view_h = wy1 - wy0

        # Composite and draw tiles per layer for the current frame
        frame = self.project.frames[self.project.current_frame]

        for layer in frame.layers:
            if not layer.visible:
                continue
            for tile in layer.canvas.iter_tiles_in_rect(wx0, wy0, view_w, view_h):
                if tile.data is None:
                    continue
                tx, ty = tile.coord
                arr = tile.data
                try:
                    qimg = numpy_to_qimage(arr)
                except Exception:
                    continue
                world_x = tx * layer.canvas.tile_size
                world_y = ty * layer.canvas.tile_size
                sx, sy = self.viewport.world_to_screen(world_x, world_y)
                dest_x = int(round(sx))
                dest_y = int(round(sy))
                dpr = self.devicePixelRatioF()
                if dpr != 1.0:
                    qimg.setDevicePixelRatio(dpr)
                painter.drawImage(dest_x, dest_y, qimg)

        # Draw preview overlay (if any)
        if self._preview_qimage is not None and self._preview_world_pos is not None:
            px, py = self._preview_world_pos
            sx, sy = self.viewport.world_to_screen(px, py)
            dest_x = int(round(sx))
            dest_y = int(round(sy))
            qimg = self._preview_qimage
            dpr = self.devicePixelRatioF()
            if dpr != 1.0:
                qimg.setDevicePixelRatio(dpr)
            painter.drawImage(dest_x, dest_y, qimg)

        # If we are in corner-picking mode, draw the points
        if self._corner_pick_target is not None and self._corner_points:
            pen = painter.pen()
            pen.setColor(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            for x, y in self._corner_points:
                sx, sy = self.viewport.world_to_screen(x, y)
                painter.drawEllipse(int(round(sx)) - 4, int(round(sy)) - 4, 8, 8)

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
            # If corner pick mode is active, capture a world point
            if self._corner_pick_target is not None:
                world = self.viewport.screen_to_world(float(event.x()), float(event.y()))
                self._corner_points.append((world[0], world[1]))
                # If we have 4 points, set them and exit mode
                if len(self._corner_points) == 4:
                    try:
                        self._corner_pick_target.set_corners(self._corner_points)
                    except Exception:
                        pass
                    self._corner_pick_target = None
                    self._corner_points = []
                    self.setCursor(Qt.ArrowCursor)
                    self.update()
                else:
                    self.update()
                return

            # Start drawing
            self._last_mouse_pos = (event.x(), event.y())
            self._current_edits = []
            world = self.viewport.screen_to_world(float(event.x()), float(event.y()))
            # Eyedropper immediate pick
            if hasattr(self.active_tool, "pick"):
                try:
                    col = self.active_tool.pick(world[0], world[1], self.project)
                    if col is not None:
                        qcol = QtColor(col[0], col[1], col[2], col[3])
                        self.colorPicked.emit(qcol)
                except Exception:
                    pass
            else:
                if hasattr(self.active_tool, "start") and hasattr(self.active_tool, "finish"):
                    try:
                        self.active_tool.start(world)
                    except Exception:
                        pass
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
        world = self.viewport.screen_to_world(float(event.x()), float(event.y()))
        if buttons & Qt.LeftButton and self._last_mouse_pos is not None:
            last = self._last_mouse_pos
            current = (event.x(), event.y())
            if hasattr(self.active_tool, "update") and hasattr(self.active_tool, "get_preview"):
                try:
                    self.active_tool.update(world)
                    preview_arr, px, py = self.active_tool.get_preview()
                    try:
                        qimg = numpy_to_qimage(preview_arr)
                        self._preview_qimage = qimg
                        self._preview_world_pos = (px, py)
                        self._invalidate_preview(px, py, preview_arr.shape[1], preview_arr.shape[0])
                    except Exception:
                        self._preview_qimage = None
                        self._preview_world_pos = None
                except Exception:
                    pass
            else:
                lx, ly = self.viewport.screen_to_world(float(last[0]), float(last[1]))
                cx, cy = self.viewport.screen_to_world(float(current[0]), float(current[1]))
                frame = self.project.frames[self.project.current_frame]
                if not frame.layers:
                    frame.add_layer()
                layer = frame.layers[0]
                if hasattr(self.active_tool, "fill"):
                    pass
                elif hasattr(self.active_tool, "apply_at"):
                    try:
                        edits = self.active_tool.apply_at(int(round(cx)), int(round(cy)), layer.canvas)
                        if edits:
                            cmd = TileEditCommand(layer.canvas, edits)
                            self.history.push(cmd)
                            self._invalidate_edits(edits, layer.canvas.tile_size)
                    except Exception:
                        pass
                else:
                    edits = self.active_tool.stroke((lx, ly), (cx, cy), layer.canvas)
                    self._current_edits.extend(edits)
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
            world = self.viewport.screen_to_world(float(event.x()), float(event.y()))
            # Bucket tool
            if hasattr(self.active_tool, "fill"):
                frame = self.project.frames[self.project.current_frame]
                if not frame.layers:
                    frame.add_layer()
                layer = frame.layers[0]
                try:
                    edits = self.active_tool.fill(int(round(world[0])), int(round(world[1])), layer.canvas, (0,0,0,255))
                except Exception:
                    edits = []
                if edits:
                    cmd = TileEditCommand(layer.canvas, edits)
                    self.history.push(cmd)
                    self._invalidate_edits(edits, layer.canvas.tile_size)
            elif hasattr(self.active_tool, "finish") and hasattr(self.active_tool, "get_preview"):
                frame = self.project.frames[self.project.current_frame]
                if not frame.layers:
                    frame.add_layer()
                layer = frame.layers[0]
                try:
                    edits = self.active_tool.finish(layer.canvas)
                except Exception:
                    edits = []
                if edits:
                    cmd = TileEditCommand(layer.canvas, edits)
                    self.history.push(cmd)
                self._preview_qimage = None
                self._preview_world_pos = None
                self.update()
            else:
                if self._current_edits:
                    cmd = TileEditCommand(self.project.frames[self.project.current_frame].layers[0].canvas, self._current_edits)
                    self.history.push(cmd)
                    self._current_edits = []
                self.update()
        super().mouseReleaseEvent(event)

    def _invalidate_edits(self, edits: list[tuple[int, int, np.ndarray, np.ndarray]], tile_size: int) -> None:
        if not edits:
            return
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

    def _invalidate_preview(self, world_x: int, world_y: int, w: int, h: int) -> None:
        sx0, sy0 = self.viewport.world_to_screen(world_x, world_y)
        sx1, sy1 = self.viewport.world_to_screen(world_x + w, world_y + h)
        x0, y0 = int(math.floor(min(sx0, sx1))), int(math.floor(min(sy0, sy1)))
        x1, y1 = int(math.ceil(max(sx0, sx1))), int(math.ceil(max(sy0, sy1)))
        rect = QRect(x0, y0, max(1, x1 - x0), max(1, y1 - y0))
        self.update(rect)

    # Public API to enter corner-picking mode for a ReferenceImage
    def enter_corner_pick_mode(self, ref) -> None:
        if getattr(ref, 'locked', False):
            return
        self._corner_pick_target = ref
        self._corner_points = []
        self.setCursor(Qt.CrossCursor)
        self.update()

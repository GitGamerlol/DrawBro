from __future__ import annotations

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QWheelEvent, QColor
from PySide6.QtCore import Qt, QRect
import numpy as np
from typing import Optional, Tuple

from core.viewport import Viewport
from core.project import Project
from core.frame import Frame
from core.history import HistoryManager
from core.commands import TileEditCommand
from tools.pen import PenTool
from tools.eraser import EraserTool


class CanvasWidget(QWidget):
    """Widget responsible for rendering the tiled canvas and routing input to tools.

    Features implemented:
    - Renders composited visible layers for the active frame by drawing tiles into the widget
    - Middle-button panning
    - Mouse-wheel zoom (smooth), with zoom centering on cursor
    - Left-button drawing using the active tool (Pen or Eraser)
    """

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

        # For now composite layers by reading tiles and drawing each tile image at the right place
        # We iterate tiles intersecting visible area for each layer and paint them in order
        for layer in frame.layers:
            if not layer.visible:
                continue
            for tile in layer.canvas.iter_tiles_in_rect(wx0, wy0, view_w, view_h):
                if tile.data is None:
                    continue
                tx, ty = tile.coord
                tile_px = tile.data.copy()  # copy to avoid sharing issues
                h_t, w_t, _ = tile_px.shape
                # Convert to QImage (RGBA8888)
                arr = tile_px
                qimg = QImage(arr.tobytes(), w_t, h_t, QImage.Format_RGBA8888)
                # Tile top-left world coords
                world_x = tx * layer.canvas.tile_size
                world_y = ty * layer.canvas.tile_size
                # Convert to screen coords
                sx, sy = self.viewport.world_to_screen(world_x, world_y)
                dest_x = int(round(sx))
                dest_y = int(round(sy))
                painter.drawImage(dest_x, dest_y, qimg)

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Smooth zoom: scale factor per wheel notch
        angle = event.angleDelta().y()
        if angle == 0:
            return
        steps = angle / 120.0
        factor = 1.0 + (0.1 * steps)
        pos = event.position()
        self.viewport.zoom_at(factor, pos.x(), pos.y())
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
            self._last_mouse_pos = current
            self.update()
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
                self._current_edits = []
            self.update()
        super().mouseReleaseEvent(event)


if __name__ == "__main__":
    import sys
    from ui.main_window import MainWindow
    app = QApplication(sys.argv)
    w = CanvasWidget(Project())
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())

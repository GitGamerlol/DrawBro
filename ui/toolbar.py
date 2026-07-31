from __future__ import annotations

from PySide6.QtWidgets import QWidget, QToolBar, QAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


class ToolBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        bar = QToolBar("Tools", self)
        # Placeholder actions — icons omitted for brevity
        self.pen_action = QAction("Pen", self)
        self.eraser_action = QAction("Eraser", self)
        self.line_action = QAction("Line", self)
        self.rect_action = QAction("Rectangle", self)
        self.ellipse_action = QAction("Ellipse", self)
        # Default checkable to show selection
        for a in (self.pen_action, self.eraser_action, self.line_action, self.rect_action, self.ellipse_action):
            a.setCheckable(True)
        # Group behavior not strictly necessary here; MainWindow will manage toggles
        bar.addAction(self.pen_action)
        bar.addAction(self.eraser_action)
        bar.addAction(self.line_action)
        bar.addAction(self.rect_action)
        bar.addAction(self.ellipse_action)
        self._bar = bar

    def widget(self):
        return self._bar

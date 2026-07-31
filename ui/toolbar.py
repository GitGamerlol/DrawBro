from __future__ import annotations
from PySide6.QtWidgets import QWidget, QToolBar, QAction
from PySide6.QtGui import QIcon


class ToolBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        bar = QToolBar("Tools", self)
        # Placeholder actions — icons omitted for brevity
        self.pen_action = QAction("Pen", self)
        self.eraser_action = QAction("Eraser", self)
        bar.addAction(self.pen_action)
        bar.addAction(self.eraser_action)
        layout = bar
        self._bar = bar

    def widget(self):
        return self._bar

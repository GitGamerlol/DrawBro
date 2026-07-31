from __future__ import annotations

from PySide6.QtWidgets import QWidget, QToolBar, QSpinBox, QCheckBox, QLabel
from PySide6.QtGui import QAction
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
        self.bucket_action = QAction("Bucket", self)
        self.eyedrop_action = QAction("Eyedropper", self)
        # Default checkable to show selection
        for a in (self.pen_action, self.eraser_action, self.line_action, self.rect_action, self.ellipse_action, self.bucket_action, self.eyedrop_action):
            a.setCheckable(True)
        # Add actions
        bar.addAction(self.pen_action)
        bar.addAction(self.eraser_action)
        bar.addAction(self.line_action)
        bar.addAction(self.rect_action)
        bar.addAction(self.ellipse_action)
        bar.addAction(self.bucket_action)
        bar.addAction(self.eyedrop_action)

        # Stroke width control
        bar.addSeparator()
        lbl = QLabel("Stroke:")
        bar.addWidget(lbl)
        self.stroke_spin = QSpinBox()
        self.stroke_spin.setRange(1, 200)
        self.stroke_spin.setValue(3)
        bar.addWidget(self.stroke_spin)

        # Fill toggle
        self.fill_checkbox = QCheckBox("Fill")
        self.fill_checkbox.setChecked(False)
        bar.addWidget(self.fill_checkbox)

        self._bar = bar

    def widget(self):
        return self._bar

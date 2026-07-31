"""
Simple color panel with current color and recent swatches.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QColorDialog
from PySide6.QtGui import QColor


class ColorPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current = QColor(0, 0, 0)
        self.recent: list[QColor] = []
        layout = QVBoxLayout()
        self._swatch = QLabel()
        self._swatch.setFixedSize(64, 64)
        self._update_swatch()
        btn = QPushButton("Choose")
        btn.clicked.connect(self._choose)
        layout.addWidget(self._swatch)
        layout.addWidget(btn)
        self.setLayout(layout)

    def _update_swatch(self) -> None:
        c = self.current
        self._swatch.setStyleSheet(f"background: rgba({c.red()},{c.green()},{c.blue()},{c.alpha()});")

    def _choose(self) -> None:
        col = QColorDialog.getColor(self.current, self)
        if col.isValid():
            self.current = col
            self.recent.insert(0, col)
            if len(self.recent) > 10:
                self.recent.pop()
            self._update_swatch()

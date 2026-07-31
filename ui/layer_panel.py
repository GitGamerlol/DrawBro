"""
Layer panel: basic UI for listing layers and adding/removing.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
from core.frame import Frame


class LayerPanel(QWidget):
    def __init__(self, frame: Frame, parent=None) -> None:
        super().__init__(parent)
        self.frame = frame
        layout = QVBoxLayout()
        self.list = QListWidget()
        self.add_btn = QPushButton("Add Layer")
        self.remove_btn = QPushButton("Remove Layer")
        self.add_btn.clicked.connect(self._add)
        self.remove_btn.clicked.connect(self._remove)
        layout.addWidget(self.list)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for i, layer in enumerate(self.frame.layers):
            item = QListWidgetItem(f"{i}: {layer.name}")
            self.list.addItem(item)

    def _add(self) -> None:
        self.frame.add_layer()
        self.refresh()

    def _remove(self) -> None:
        idx = self.list.currentRow()
        if idx >= 0:
            self.frame.remove_layer(idx)
            self.refresh()

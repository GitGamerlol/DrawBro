"""
Layer panel UI with controls to rename, duplicate, delete, reorder, opacity, visibility, and lock.
Calls controller methods on actions so the MainWindow (controller) can create history commands.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QHBoxLayout, QLineEdit, QLabel, QSlider, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from core.frame import Frame


class LayerPanel(QWidget):
    def __init__(self, frame: Frame, controller, parent=None) -> None:
        super().__init__(parent)
        self.frame = frame
        self.controller = controller
        layout = QVBoxLayout()
        self.list = QListWidget()

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.dup_btn = QPushButton("Duplicate")
        self.remove_btn = QPushButton("Remove")
        self.up_btn = QPushButton("Up")
        self.down_btn = QPushButton("Down")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.dup_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.up_btn)
        btn_layout.addWidget(self.down_btn)

        self.name_edit = QLineEdit()
        self.rename_btn = QPushButton("Rename")

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_label = QLabel("Opacity: 100%")

        self.visible_check = QCheckBox("Visible")
        self.lock_check = QCheckBox("Locked")

        layout.addWidget(self.list)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.opacity_label)
        layout.addWidget(self.opacity_slider)
        layout.addWidget(self.visible_check)
        layout.addWidget(self.lock_check)
        self.setLayout(layout)

        # Connect signals
        self.add_btn.clicked.connect(self._add)
        self.remove_btn.clicked.connect(self._remove)
        self.dup_btn.clicked.connect(self._duplicate)
        self.up_btn.clicked.connect(self._move_up)
        self.down_btn.clicked.connect(self._move_down)
        self.rename_btn.clicked.connect(self._rename)
        self.opacity_slider.valueChanged.connect(self._opacity_changed)
        self.visible_check.toggled.connect(self._visible_toggled)
        self.lock_check.toggled.connect(self._lock_toggled)
        self.list.currentRowChanged.connect(self._on_selection_changed)

        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for i, layer in enumerate(self.frame.layers):
            item = QListWidgetItem(f"{i}: {layer.name}")
            self.list.addItem(item)
        # update controls based on current selection
        self._on_selection_changed(self.list.currentRow())

    def _add(self) -> None:
        # ask controller to add layer
        self.controller.add_layer()
        self.refresh()

    def _remove(self) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        confirm = QMessageBox.question(self, "Remove Layer", f"Delete layer {idx}?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.controller.remove_layer(idx)
            self.refresh()

    def _duplicate(self) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        self.controller.duplicate_layer(idx)
        self.refresh()

    def _move_up(self) -> None:
        idx = self.list.currentRow()
        if idx <= 0:
            return
        self.controller.move_layer(idx, idx - 1)
        self.refresh()
        self.list.setCurrentRow(idx - 1)

    def _move_down(self) -> None:
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.frame.layers) - 1:
            return
        self.controller.move_layer(idx, idx + 1)
        self.refresh()
        self.list.setCurrentRow(idx + 1)

    def _rename(self) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        name = self.name_edit.text().strip()
        if not name:
            return
        self.controller.rename_layer(idx, name)
        self.refresh()

    def _opacity_changed(self, val: int) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        opacity = val / 100.0
        self.opacity_label.setText(f"Opacity: {val}%")
        self.controller.change_layer_opacity(idx, opacity)

    def _visible_toggled(self, checked: bool) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        self.controller.toggle_visible(idx)
        self.refresh()

    def _lock_toggled(self, checked: bool) -> None:
        idx = self.list.currentRow()
        if idx < 0:
            return
        self.controller.toggle_lock(idx)
        self.refresh()

    def _on_selection_changed(self, row: int) -> None:
        if row < 0 or row >= len(self.frame.layers):
            self.name_edit.setText("")
            self.opacity_slider.setValue(100)
            self.visible_check.setChecked(True)
            self.lock_check.setChecked(False)
            return
        layer = self.frame.layers[row]
        self.name_edit.setText(layer.name)
        self.opacity_slider.setValue(int(round(layer.opacity * 100)))
        self.visible_check.setChecked(layer.visible)
        self.lock_check.setChecked(layer.locked)

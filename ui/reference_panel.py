from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QCheckBox, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from core.project import Project
from reference.perspective import ReferenceImage
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap


class ReferencePanel(QWidget):
    """Panel to control reference images: load, opacity, lock, hide, and corner-picking mode.

    It emits a signal when the canvas should enter corner-picking mode for the latest reference.
    """

    pickCorners = Signal(object)  # emits ReferenceImage to pick corners for

    def __init__(self, project: Project, canvas_widget=None, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.canvas_widget = canvas_widget
        layout = QVBoxLayout()
        self.load_btn = QPushButton("Load Reference Image")
        self.pick_btn = QPushButton("Pick Corners")
        self.opacity_label = QLabel("Opacity: 75%")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(75)
        self.hide_check = QCheckBox("Hide")
        self.lock_check = QCheckBox("Lock")
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(160, 120)

        layout.addWidget(self.load_btn)
        layout.addWidget(self.pick_btn)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.opacity_label)
        layout.addWidget(self.opacity_slider)
        layout.addWidget(self.hide_check)
        layout.addWidget(self.lock_check)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self._on_load)
        self.pick_btn.clicked.connect(self._on_pick)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.hide_check.toggled.connect(self._on_hide_toggled)
        self.lock_check.toggled.connect(self._on_lock_toggled)

        self._active_ref: ReferenceImage | None = None

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open reference image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if not path:
            return
        try:
            ref = ReferenceImage.load_from_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
            return
        self.project.add_reference(ref)
        self._active_ref = ref
        # show preview
        pil = ref.get_pil_preview()
        if pil is not None:
            qim = ImageQt(pil)
            pix = QPixmap.fromImage(qim).scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pix)
        # default: enable pick corners
        self.pickCorners.emit(ref)

    def _on_pick(self) -> None:
        if self._active_ref is None:
            QMessageBox.information(self, "No reference", "Load a reference image first")
            return
        self.pickCorners.emit(self._active_ref)

    def _on_opacity_changed(self, v: int) -> None:
        self.opacity_label.setText(f"Opacity: {v}%")
        if self._active_ref is None:
            return
        self._active_ref.opacity = v / 100.0
        if self.canvas_widget:
            self.canvas_widget.update()

    def _on_hide_toggled(self, checked: bool) -> None:
        if self._active_ref is None:
            return
        self._active_ref.visible = not checked
        if self.canvas_widget:
            self.canvas_widget.update()

    def _on_lock_toggled(self, checked: bool) -> None:
        if self._active_ref is None:
            return
        self._active_ref.locked = checked

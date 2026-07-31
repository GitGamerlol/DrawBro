"""
Timeline skeleton for animation controls.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel


class TimelineWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.fps_label = QLabel("FPS: 12")
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.fps_label)
        self.setLayout(layout)

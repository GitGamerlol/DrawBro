"""
Main window skeleton (PySide6). This file creates the main window and
provides placeholder areas for the canvas and panels.

Later: implement a CanvasWidget that renders from core.Frame and Viewport,
connect to toolbar, layer panel, timeline, etc.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStatusBar
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from core.viewport import Viewport
from core.project import Project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DrawBro")
        self.resize(1200, 800)
        self._apply_dark_theme()

        # Document model
        self.project = Project()
        self.viewport = Viewport()

        # Central canvas placeholder (will be replaced by CanvasWidget)
        central = QWidget()
        layout = QHBoxLayout()
        central.setLayout(layout)

        canvas_area = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_area.setLayout(canvas_layout)
        canvas_layout.addWidget(QLabel("Canvas will appear here (CanvasWidget)"))
        layout.addWidget(canvas_area, 1)

        # Right-side placeholder for panels
        panels = QWidget()
        panels_layout = QVBoxLayout()
        panels.setLayout(panels_layout)
        panels_layout.addWidget(QLabel("Layer Panel"))
        panels_layout.addWidget(QLabel("Color Panel"))
        layout.addWidget(panels)

        self.setCentralWidget(central)

        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _apply_dark_theme(self) -> None:
        pal = self.palette()
        base = QColor(30, 30, 30)
        pal.setColor(QPalette.Window, base)
        pal.setColor(QPalette.WindowText, QColor(220, 220, 220))
        pal.setColor(QPalette.Base, QColor(40, 40, 40))
        pal.setColor(QPalette.Text, QColor(230, 230, 230))
        pal.setColor(QPalette.Button, QColor(50, 50, 50))
        self.setPalette(pal)

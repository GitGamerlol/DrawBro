from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStatusBar, QSplitter
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from core.viewport import Viewport
from core.project import Project
from ui.canvas_widget import CanvasWidget
from ui.toolbar import ToolBar
from ui.color_panel import ColorPanel
from ui.layer_panel import LayerPanel
from animation.timeline import TimelineWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DrawBro")
        self.resize(1200, 800)
        self._apply_dark_theme()

        # Document model
        self.project = Project()
        self.viewport = Viewport()

        # Create widgets
        self.canvas_widget = CanvasWidget(self.project, self.viewport)
        self.toolbar = ToolBar()
        self.color_panel = ColorPanel()
        self.layer_panel = LayerPanel(self.project.frames[0])
        self.timeline = TimelineWidget()

        # Layout using splitter
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)

        top_bar = self.toolbar.widget()
        layout.addWidget(top_bar)

        splitter = QSplitter()
        canvas_area = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_area.setLayout(canvas_layout)
        canvas_layout.addWidget(self.canvas_widget)
        splitter.addWidget(canvas_area)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        right_layout.addWidget(self.layer_panel)
        right_layout.addWidget(self.color_panel)
        splitter.addWidget(right_panel)

        layout.addWidget(splitter)
        layout.addWidget(self.timeline)

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

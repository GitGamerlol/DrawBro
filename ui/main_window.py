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
from tools.pen import PenTool
from tools.eraser import EraserTool
from tools.shape_tools import LineTool, RectangleTool, EllipseTool


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

        # Additional tools
        self.pen_tool = self.canvas_widget.pen_tool
        self.eraser_tool = self.canvas_widget.eraser_tool
        self.line_tool = LineTool()
        self.rect_tool = RectangleTool()
        self.ellipse_tool = EllipseTool()

        # Connect color panel to pen tool color
        self.color_panel.color_changed.connect(self._on_color_changed)
        # Connect canvas zoom changes to status bar display
        # Will set initial message after status bar created

        # Connect toolbar actions to select tools
        self.toolbar.pen_action.triggered.connect(self._select_pen)
        self.toolbar.eraser_action.triggered.connect(self._select_eraser)
        self.toolbar.line_action.triggered.connect(self._select_line)
        self.toolbar.rect_action.triggered.connect(self._select_rect)
        self.toolbar.ellipse_action.triggered.connect(self._select_ellipse)
        # Default selection
        self.toolbar.pen_action.setChecked(True)

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

        # Now connect zoomChanged so the status bar updates
        self.canvas_widget.zoomChanged.connect(self._on_zoom_changed)
        self._on_zoom_changed(self.viewport.zoom)

    def _select_pen(self) -> None:
        self._uncheck_all()
        self.toolbar.pen_action.setChecked(True)
        self.canvas_widget.active_tool = self.pen_tool

    def _select_eraser(self) -> None:
        self._uncheck_all()
        self.toolbar.eraser_action.setChecked(True)
        self.canvas_widget.active_tool = self.eraser_tool

    def _select_line(self) -> None:
        self._uncheck_all()
        self.toolbar.line_action.setChecked(True)
        self.canvas_widget.active_tool = self.line_tool

    def _select_rect(self) -> None:
        self._uncheck_all()
        self.toolbar.rect_action.setChecked(True)
        self.canvas_widget.active_tool = self.rect_tool

    def _select_ellipse(self) -> None:
        self._uncheck_all()
        self.toolbar.ellipse_action.setChecked(True)
        self.canvas_widget.active_tool = self.ellipse_tool

    def _uncheck_all(self) -> None:
        for a in (self.toolbar.pen_action, self.toolbar.eraser_action, self.toolbar.line_action, self.toolbar.rect_action, self.toolbar.ellipse_action):
            a.setChecked(False)

    def _on_color_changed(self, color: QColor) -> None:
        rgba = (color.red(), color.green(), color.blue(), color.alpha())
        # Update pen tool color
        self.canvas_widget.pen_tool.color = rgba
        # Also update fill/stroke colors for shape tools
        self.line_tool.stroke_color = rgba
        self.rect_tool.stroke_color = rgba
        self.rect_tool.fill_color = rgba
        self.ellipse_tool.stroke_color = rgba
        self.ellipse_tool.fill_color = rgba

    def _on_zoom_changed(self, zoom: float) -> None:
        self.statusBar().showMessage(f"Zoom: {zoom:.2f}x")

    def _apply_dark_theme(self) -> None:
        pal = self.palette()
        base = QColor(30, 30, 30)
        pal.setColor(QPalette.Window, base)
        pal.setColor(QPalette.WindowText, QColor(220, 220, 220))
        pal.setColor(QPalette.Base, QColor(40, 40, 40))
        pal.setColor(QPalette.Text, QColor(230, 230, 230))
        pal.setColor(QPalette.Button, QColor(50, 50, 50))
        self.setPalette(pal)

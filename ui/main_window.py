from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStatusBar,
    QSplitter
)
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
from tools.bucket import BucketTool
from tools.eyedropper import EyedropperTool
from tools.smooth import SmoothTool

from core.layer_commands import (
    AddLayerCommand,
    RemoveLayerCommand,
    DuplicateLayerCommand,
    RenameLayerCommand,
    MoveLayerCommand,
    ChangeLayerOpacityCommand,
    ToggleVisibilityCommand,
    ToggleLockCommand
)

from core.history import HistoryManager


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("DrawBro")
        self.resize(1200, 800)
        self._apply_dark_theme()

        # Document
        self.project = Project()
        self.viewport = Viewport()

        # History
        self.history = HistoryManager()

        # Widgets
        self.canvas_widget = CanvasWidget(self.project, self.viewport)
        self.toolbar = ToolBar()
        self.color_panel = ColorPanel()

        self.layer_panel = LayerPanel(
            self.project.frames[self.project.current_frame],
            controller=self
        )

        self.timeline = TimelineWidget(self.project)

        # Tools
        self.pen_tool = self.canvas_widget.pen_tool
        self.eraser_tool = self.canvas_widget.eraser_tool

        self.line_tool = LineTool()
        self.rect_tool = RectangleTool()
        self.ellipse_tool = EllipseTool()
        self.bucket_tool = BucketTool()
        self.eyedrop_tool = EyedropperTool()
        self.smooth_tool = SmoothTool()

        # Connections
        self.color_panel.color_changed.connect(self._on_color_changed)

        self.toolbar.pen_action.triggered.connect(self._select_pen)
        self.toolbar.eraser_action.triggered.connect(self._select_eraser)
        self.toolbar.line_action.triggered.connect(self._select_line)
        self.toolbar.rect_action.triggered.connect(self._select_rect)
        self.toolbar.ellipse_action.triggered.connect(self._select_ellipse)
        self.toolbar.bucket_action.triggered.connect(self._select_bucket)
        self.toolbar.eyedrop_action.triggered.connect(self._select_eyedrop)

        self.toolbar.pen_action.setChecked(True)

        self.toolbar.stroke_spin.valueChanged.connect(
            self._on_stroke_width_changed
        )

        self.toolbar.fill_checkbox.toggled.connect(
            self._on_fill_toggled
        )

        self.canvas_widget.colorPicked.connect(
            self._on_color_picked
        )

        self.timeline.frameChanged.connect(
            self._on_frame_changed
        )

        self.timeline.playToggled.connect(
            self._on_play_toggled
        )

        # ============================
        # FIXED LAYOUT
        # ============================

        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Toolbar
        main_layout.addWidget(self.toolbar.widget())

        # Main area
        splitter = QSplitter(Qt.Horizontal)

        # Canvas side
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        canvas_container.setLayout(canvas_layout)

        self.canvas_widget.setMinimumSize(500, 500)

        canvas_layout.addWidget(self.canvas_widget)

        splitter.addWidget(canvas_container)

        # Side panels
        side_panel = QWidget()
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(0, 0, 0, 0)

        side_panel.setLayout(side_layout)

        side_layout.addWidget(self.layer_panel)
        side_layout.addWidget(self.color_panel)

        splitter.addWidget(side_panel)

        # Canvas gets most space
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)

        splitter.setSizes([
            900,
            300
        ])

        main_layout.addWidget(splitter, 1)

        # Timeline
        main_layout.addWidget(self.timeline)

        self.setCentralWidget(central)

        # Status
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

        self.canvas_widget.zoomChanged.connect(
            self._on_zoom_changed
        )

        self._on_zoom_changed(
            self.viewport.zoom
        )


    def _on_frame_changed(self, idx: int):
        self.layer_panel.frame = self.project.frames[
            self.project.current_frame
        ]

        self.layer_panel.refresh()
        self.canvas_widget.update()


    def _on_play_toggled(self, playing: bool):
        pass


    # Layer controls

    def add_layer(self):
        cmd = AddLayerCommand(
            self.project.frames[self.project.current_frame]
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def remove_layer(self, index):
        cmd = RemoveLayerCommand(
            self.project.frames[self.project.current_frame],
            index
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def duplicate_layer(self, index):
        cmd = DuplicateLayerCommand(
            self.project.frames[self.project.current_frame],
            index
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def rename_layer(self, index, name):
        cmd = RenameLayerCommand(
            self.project.frames[self.project.current_frame],
            index,
            name
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def move_layer(self, src, dst):
        cmd = MoveLayerCommand(
            self.project.frames[self.project.current_frame],
            src,
            dst
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def change_layer_opacity(self, index, opacity):
        cmd = ChangeLayerOpacityCommand(
            self.project.frames[self.project.current_frame],
            index,
            opacity
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def toggle_visible(self, index):
        cmd = ToggleVisibilityCommand(
            self.project.frames[self.project.current_frame],
            index
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    def toggle_lock(self, index):
        cmd = ToggleLockCommand(
            self.project.frames[self.project.current_frame],
            index
        )
        self.history.push(cmd)
        self.layer_panel.refresh()


    # Tools

    def _select_pen(self):
        self._uncheck_all()
        self.toolbar.pen_action.setChecked(True)
        self.canvas_widget.active_tool = self.pen_tool


    def _select_eraser(self):
        self._uncheck_all()
        self.toolbar.eraser_action.setChecked(True)
        self.canvas_widget.active_tool = self.eraser_tool


    def _select_line(self):
        self._uncheck_all()
        self.toolbar.line_action.setChecked(True)
        self.canvas_widget.active_tool = self.line_tool


    def _select_rect(self):
        self._uncheck_all()
        self.toolbar.rect_action.setChecked(True)
        self.canvas_widget.active_tool = self.rect_tool


    def _select_ellipse(self):
        self._uncheck_all()
        self.toolbar.ellipse_action.setChecked(True)
        self.canvas_widget.active_tool = self.ellipse_tool


    def _select_bucket(self):
        self._uncheck_all()
        self.toolbar.bucket_action.setChecked(True)
        self.canvas_widget.active_tool = self.bucket_tool


    def _select_eyedrop(self):
        self._uncheck_all()
        self.toolbar.eyedrop_action.setChecked(True)
        self.canvas_widget.active_tool = self.eyedrop_tool


    def _on_color_changed(self, color):
        rgba = (
            color.red(),
            color.green(),
            color.blue(),
            color.alpha()
        )

        self.canvas_widget.pen_tool.color = rgba

        self.line_tool.stroke_color = rgba
        self.rect_tool.stroke_color = rgba
        self.rect_tool.fill_color = rgba
        self.ellipse_tool.stroke_color = rgba
        self.ellipse_tool.fill_color = rgba


    def _on_color_picked(self, color):
        self.color_panel.current = color
        self.color_panel._update_swatch()
        self._on_color_changed(color)


    def _on_zoom_changed(self, zoom):
        self.statusBar().showMessage(
            f"Zoom: {zoom:.2f}x"
        )


    def _on_stroke_width_changed(self, val):
        self.pen_tool.size = float(val)
        self.line_tool.stroke_width = val
        self.rect_tool.stroke_width = val
        self.ellipse_tool.stroke_width = val


    def _on_fill_toggled(self, checked):
        self.rect_tool.fill = checked
        self.ellipse_tool.fill = checked


    def _uncheck_all(self):
        actions = [
            self.toolbar.pen_action,
            self.toolbar.eraser_action,
            self.toolbar.line_action,
            self.toolbar.rect_action,
            self.toolbar.ellipse_action,
            self.toolbar.bucket_action,
            self.toolbar.eyedrop_action
        ]

        for action in actions:
            action.setChecked(False)


    def _apply_dark_theme(self):
        pal = self.palette()

        pal.setColor(
            QPalette.Window,
            QColor(30, 30, 30)
        )

        pal.setColor(
            QPalette.WindowText,
            QColor(220, 220, 220)
        )

        pal.setColor(
            QPalette.Base,
            QColor(40, 40, 40)
        )

        pal.setColor(
            QPalette.Text,
            QColor(230, 230, 230)
        )

        pal.setColor(
            QPalette.Button,
            QColor(50, 50, 50)
        )

        self.setPalette(pal)
